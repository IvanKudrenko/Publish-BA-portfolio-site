"""BA Blog integration checks. Never binds a socket, pushes, or touches production content."""
import base64, io, json, subprocess, tempfile, threading, unittest
from pathlib import Path
from types import SimpleNamespace
import blog

class BlogFlow(unittest.TestCase):
    def setUp(self):
        names=("ROOT","PRIVATE","PRIVATE_POSTS","PRIVATE_MEDIA","POSTS","PUBLIC_ASSETS")
        self.original={name:getattr(blog,name) for name in names}; self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name)
        blog.ROOT=root; blog.PRIVATE=root/".blog-private"; blog.PRIVATE_POSTS=blog.PRIVATE/"posts"; blog.PRIVATE_MEDIA=blog.PRIVATE/"media"; blog.POSTS=root/"content/posts"; blog.PUBLIC_ASSETS=root/"blog/assets"
        for folder in (blog.PRIVATE_POSTS,blog.PRIVATE_MEDIA,blog.POSTS,root/"blog"): folder.mkdir(parents=True,exist_ok=True)
        (root/"index.html").write_text((self.original["ROOT"]/"index.html").read_text())
        self.server=SimpleNamespace(server_port=8787,session="test",password="test",push=False,lock=threading.Lock(),branch="main")
    def tearDown(self):
        for name,value in self.original.items(): setattr(blog,name,value)
        self.temp.cleanup()
    def action(self,route,payload,authenticated=True,origin=True,headers=None,raw=False):
        handler=object.__new__(blog.Handler); handler.server=self.server; handler.path="/api/"+route
        body=payload if raw else json.dumps(payload).encode(); handler.rfile=io.BytesIO(body)
        handler.headers={"Host":"127.0.0.1:8787","Origin":"http://127.0.0.1:8787" if origin else "https://evil.test","Content-Length":str(len(body)),"Cookie":"ba_session=test" if authenticated else "",**(headers or {})}
        result={}; handler.reply=lambda value,status=200:result.update(value=value,status=status); handler.do_POST(); return result
    def post(self):
        return {"schemaVersion":2,"id":"1"*24,"type":"post","status":"draft","title":"","slug":"exact-first-thought","description":"","text":"One short **Post**.","originalThought":"  i THink…\n\nexactly this!  ","link":"https://example.com","blocks":[],"imageIds":[],"coverMediaId":"","media":[],"tags":[],"seo":{},"layout":{},"redirects":[],"createdAt":"2026-10-05T12:00:00Z","updatedAt":"","publishedAt":""}
    def test_post_draft_publish_update_redirect_and_unpublish(self):
        post=self.post(); self.assertEqual(self.action("save",post,False)["status"],401); self.assertEqual(self.action("save",post,origin=False)["status"],403)
        saved=self.action("save",post); self.assertEqual(saved["status"],200); stored=json.loads(next(blog.PRIVATE_POSTS.glob("*.json")).read_text()); self.assertEqual(stored["originalThought"],post["originalThought"])
        blog.build(); self.assertNotIn("One short",(blog.ROOT/"blog/index.html").read_text()); self.assertNotIn("exact-first-thought",(blog.ROOT/"sitemap.xml").read_text()); self.assertNotIn("One short",(blog.ROOT/"blog/feed.xml").read_text())
        preview=self.action("preview",post)["value"]["html"]; self.assertIn("  i THink…\n\nexactly this!  ",preview); self.assertIn("<strong>Post</strong>",preview)
        published=self.action("publish",post)["value"]["post"]; self.assertTrue((blog.ROOT/"blog/exact-first-thought/index.html").exists()); self.assertIn("exact-first-thought",(blog.ROOT/"sitemap.xml").read_text()); self.assertIn("One short",(blog.ROOT/"blog/feed.xml").read_text())
        published["slug"]="changed-thought"; updated=self.action("publish",published)["value"]["post"]; self.assertIn("exact-first-thought",updated["redirects"]); self.assertIn("/blog/changed-thought/",(blog.ROOT/"blog/exact-first-thought/index.html").read_text())
        self.action("unpublish",updated); self.assertFalse((blog.ROOT/"blog/changed-thought/index.html").exists()); self.assertNotIn("changed-thought",(blog.ROOT/"sitemap.xml").read_text()); self.assertTrue(list(blog.PRIVATE_POSTS.glob("*.json")))
        self.action("delete",updated); self.assertFalse(list(blog.PRIVATE_POSTS.glob("*.json")))
    def test_article_blocks_sanitization_and_media(self):
        article=self.post(); article.update({"id":"2"*24,"type":"article","title":"A structured article","slug":"structured-article","text":"","originalThought":"","blocks":[{"id":"a","type":"heading","level":2,"text":"Section"},{"id":"b","type":"paragraph","text":"Readable **writing**."},{"id":"c","type":"original-thought","text":"Do NOT change This."},{"id":"d","type":"html","html":"<p onclick=\"bad()\">Safe</p><script>alert(1)</script>"}]})
        rendered=blog.entry_html(article,True); self.assertIn("<h2",rendered); self.assertIn("Do NOT change This.",rendered); self.assertNotIn("onclick",rendered); self.assertNotIn("<script",rendered)
        png=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nL8AAAAASUVORK5CYII=")
        uploaded=self.action("upload",png,headers={"Content-Type":"image/png","X-Content-Id":article["id"],"X-Filename":"Screenshot.png"},raw=True)["value"]["media"]; uploaded["alt"]="One pixel test image"; article["media"]=[uploaded]; article["coverMediaId"]=uploaded["id"]
        result=self.action("publish",article); self.assertEqual(result["status"],200); public=result["value"]["post"]; self.assertTrue(public["media"][0]["variants"]); self.assertTrue((blog.PUBLIC_ASSETS/article["id"]).exists())
        page=(blog.ROOT/"blog/structured-article/index.html").read_text(); self.assertIn("application/ld+json",page); self.assertIn("srcset=",page); self.assertIn("One pixel test image",page)
    def test_url_and_schema_guards(self):
        self.assertEqual(blog.safe_url("javascript:alert(1)"),"#"); self.assertNotIn("javascript:",blog.inline("[unsafe](javascript:alert(1))")); self.assertIn("&lt;script&gt;",blog.markdown("<script>alert(1)</script>"))
        post=self.post(); post["slug"]="../escape"; self.assertEqual(self.action("publish",post)["status"],400)
        article=self.post(); article.update({"type":"article","title":"Empty","slug":"empty","text":"","blocks":[]}); self.assertEqual(self.action("publish",article)["status"],400)
    def test_git_publish_leaves_unrelated_staged_work_untouched(self):
        remote=tempfile.TemporaryDirectory()
        try:
            blog.build(); subprocess.run(["git","init","-b","main"],cwd=blog.ROOT,check=True,capture_output=True); subprocess.run(["git","config","user.email","writer-test@baproj.com"],cwd=blog.ROOT,check=True); subprocess.run(["git","config","user.name","BA Writer Test"],cwd=blog.ROOT,check=True)
            subprocess.run(["git","add","."],cwd=blog.ROOT,check=True); subprocess.run(["git","commit","-m","baseline"],cwd=blog.ROOT,check=True,capture_output=True); subprocess.run(["git","init","--bare",remote.name],check=True,capture_output=True); subprocess.run(["git","remote","add","origin",remote.name],cwd=blog.ROOT,check=True)
            unrelated=blog.ROOT/"unrelated.txt"; unrelated.write_text("unfinished work\n"); subprocess.run(["git","add","unrelated.txt"],cwd=blog.ROOT,check=True); self.server.push=True
            result=self.action("publish",self.post()); self.assertEqual(result["status"],200); self.assertEqual(result["value"]["state"],"pushed")
            staged=subprocess.run(["git","diff","--cached","--name-only"],cwd=blog.ROOT,check=True,capture_output=True,text=True).stdout.splitlines(); self.assertEqual(staged,["unrelated.txt"])
            committed=subprocess.run(["git","show","--pretty=","--name-only","HEAD"],cwd=blog.ROOT,check=True,capture_output=True,text=True).stdout.splitlines(); self.assertNotIn("unrelated.txt",committed); self.assertIn("content/posts/111111111111111111111111.json",committed)
        finally: remote.cleanup()

if __name__=="__main__": unittest.main()
