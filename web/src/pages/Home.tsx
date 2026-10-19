import { posts } from "../posts";
import { Link } from "../components/Link";
import { formatDate } from "../site";

export function Home() {
  return (
    <ul className="post-list">
      {posts.map((post) => (
        <li key={post.slug} className="post-list-item">
          <time className="post-date" dateTime={post.date}>
            {formatDate(post.date)}
          </time>
          <h2>
            <Link to={`/${post.slug}`}>{post.title}</Link>
          </h2>
          <p>{post.dek}</p>
        </li>
      ))}
    </ul>
  );
}
