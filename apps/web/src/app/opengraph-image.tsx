import { ImageResponse } from "next/og";

import { profile } from "@/content/profile";
import { palette } from "@/styles/palette";

export const alt = `${profile.name}, data scientist in Penang`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const SWATCHES = [palette.mustard, palette.jade, palette.cobalt, palette.rose];

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 72, background: palette.peacock, color: palette.porcelain }}>
        <div style={{ display: "flex" }}>
          {SWATCHES.map((c) => <div key={c} style={{ width: 72, height: 72, background: c, border: `4px solid ${palette.porcelain}` }} />)}
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 96, fontWeight: 800, lineHeight: 1 }}>{profile.name}</div>
          <div style={{ fontSize: 36, marginTop: 24, color: palette.onPeacock, maxWidth: 980 }}>{profile.roleLine}</div>
        </div>
      </div>
    ),
    size,
  );
}
