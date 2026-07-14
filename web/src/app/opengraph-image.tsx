import { ImageResponse } from "next/og";

export const alt = "Signal, explainable music recommendations";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "76px 86px",
        background: "linear-gradient(135deg, #0a0b0a 0%, #11160d 58%, #11101a 100%)",
        color: "#f7f7f2",
        fontFamily: "sans-serif",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", maxWidth: 720 }}>
        <div
          style={{
            display: "flex",
            color: "#c7ff5e",
            fontSize: 18,
            letterSpacing: 4,
            textTransform: "uppercase",
          }}
        >
          Explainable music discovery
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: 28,
            fontSize: 82,
            fontWeight: 620,
            letterSpacing: -5,
            lineHeight: 0.96,
          }}
        >
          <span>Music has a shape.</span>
          <span style={{ color: "#c7ff5e" }}>Find what fits.</span>
        </div>
        <div style={{ display: "flex", marginTop: 35, color: "#a9ada4", fontSize: 22 }}>
          Pick a song or mood. See why every result matched.
        </div>
      </div>

      <div
        style={{
          width: 330,
          height: 330,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "1px solid rgba(255,255,255,.15)",
          borderRadius: "50%",
          background: "radial-gradient(circle, #1d2119 0 24%, #0c0d0b 25% 100%)",
          boxShadow: "0 30px 90px rgba(0,0,0,.5)",
        }}
      >
        <div
          style={{
            width: 116,
            height: 116,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: "50%",
            background: "#c7ff5e",
            color: "#11130c",
            fontSize: 25,
            fontWeight: 750,
          }}
        >
          signal
        </div>
      </div>
    </div>,
    size,
  );
}
