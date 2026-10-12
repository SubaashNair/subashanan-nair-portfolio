import { tileMarkup, type TileSpec } from "./tile-geometry";

interface TileProps {
  spec: TileSpec;
  className?: string;
}

/** Decorative tile. The markup comes from internal constants only, so inner HTML is safe here. */
export function Tile({ spec, className }: TileProps) {
  return <svg className={className} viewBox="0 0 100 100" aria-hidden="true" dangerouslySetInnerHTML={{ __html: tileMarkup(spec) }} />;
}
