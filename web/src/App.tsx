import { Suspense, useEffect } from "react";
import { findPost } from "./posts";
import { Home } from "./pages/Home";
import { usePath } from "./lib/router";
import { Link } from "./components/Link";
import { site, formatDate } from "./site";
import "./styles.css";

function App() {
  const path = usePath();
  const slug = path.replace(/^\/+|\/+$/g, "");
  const post = slug ? findPost(slug) : null;

  useEffect(() => {
    document.title = post ? `${post.title} | ${site.name}` : site.name;
  }, [post]);

  let page;
  if (!slug) {
    page = <Home />;
  } else if (post) {
    page = (
      <>
        <time className="post-date" dateTime={post.date}>
          {formatDate(post.date)}
        </time>
        <Suspense fallback={<p>Loading…</p>}>
          <post.Component />
        </Suspense>
      </>
    );
  } else {
    page = (
      <section className="story-section">
        <h1>Not found</h1>
        <p>
          There's no post at this address. <Link to="/">Back to all posts</Link>
        </p>
      </section>
    );
  }

  return (
    <>
      <header className="site-header">
        <Link to="/" className="site-name">
          {site.name}
        </Link>
        <span className="site-tagline">{site.tagline}</span>
      </header>
      <main className="story">{page}</main>
    </>
  );
}

export default App;
