interface Props {
  src: string;
  alt: string;
  caption: string;
  side?: "left" | "right";
}

// Mirrors Deadspin's actual img.left / img.right treatment from their 2006
// stylesheet: white padding, a thin gray border, floated so body text wraps
// around it.
export function FloatImg({ src, alt, caption, side = "right" }: Props) {
  return (
    <figure className={`float-img float-img-${side}`}>
      <img src={src} alt={alt} loading="lazy" />
      <figcaption>{caption}</figcaption>
    </figure>
  );
}
