interface Props {
  src: string;
  alt: string;
  caption: string;
  side?: "left" | "right";
  /** photographer + license, for the attribution CC BY / BY-SA photos require */
  credit: { by: string; license: string };
}

// Mirrors Deadspin's actual img.left / img.right treatment from their 2006
// stylesheet: white padding, a thin gray border, floated so body text wraps
// around it.
export function FloatImg({ src, alt, caption, side = "right", credit }: Props) {
  return (
    <figure className={`float-img float-img-${side}`}>
      <img src={src} alt={alt} loading="lazy" />
      <figcaption>
        {caption}
        <span className="float-img-credit">
          Photo: <a href={commonsPage(src)}>{credit.by}</a>,{" "}
          <a href={licenseUrl(credit.license)}>{credit.license}</a>
        </span>
      </figcaption>
    </figure>
  );
}

// ".../commons/thumb/f/fd/Name.jpg/500px-Name.jpg" or ".../commons/8/8b/Name.jpg"
// -> the file's page on Wikimedia Commons
function commonsPage(src: string) {
  const parts = new URL(src).pathname.split("/");
  const i = parts.indexOf("commons") + (parts.includes("thumb") ? 4 : 3);
  return `https://commons.wikimedia.org/wiki/File:${parts[i]}`;
}

// "CC BY-SA 2.0" -> https://creativecommons.org/licenses/by-sa/2.0/
function licenseUrl(license: string) {
  const [, kind, version] = license.split(" ");
  return `https://creativecommons.org/licenses/${kind.toLowerCase()}/${version}/`;
}
