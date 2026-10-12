import Link from "next/link";

import { Mosaic } from "@/components/tiles/mosaic";
import { mixedTile } from "@/components/tiles/tile-geometry";
import { profile } from "@/content/profile";

const TILES = Array.from({ length: 16 }, (_, i) => mixedTile(i));
const [first, last] = profile.name.split(" ");

export function Hero() {
  return (
    <div className="top">
      <div className="wrap">
        <div className="hero">
          <div>
            <h1>{first}<br />{" "}{last}</h1>
            <p className="lede">{profile.roleLine}</p>
            <div className="actions">
              <Link className="btn primary" href="/work">Read the case studies</Link>
              <Link className="btn quiet" href="/about#contact">Get in touch</Link>
            </div>
          </div>
          <div>
            <Mosaic tiles={TILES} label="Decorative tile mosaic. Select a tile to turn it." />
            <p className="mosaic-note">Patterns drawn from George Town&apos;s Peranakan floor tiles. Tap a tile to turn it.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
