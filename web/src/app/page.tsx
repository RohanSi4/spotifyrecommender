import { SignalApp } from "@/components/signal-app";
import { SignalMark } from "@/components/signal-mark";

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Signal home">
          <SignalMark compact />
          <span>Signal</span>
        </a>
        <nav aria-label="Page links">
          <a href="#try-it">Try it</a>
          <a href="#method">How it works</a>
          <a href="https://github.com/RohanSi4/spotifyrecommender" target="_blank" rel="noreferrer">
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span /> Explainable music discovery</p>
          <h1>Music has a shape.<br /><em>Find what fits.</em></h1>
          <p className="hero-lede">
            Pick a song or choose the mood you want. Signal compares nine audio traits and tells
            you why every recommendation made the list.
          </p>
          <a className="hero-cta" href="#try-it">
            Find your next song <span aria-hidden="true">↓</span>
          </a>
        </div>

        <div className="hero-art" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="vinyl">
            <div className="vinyl-ring vinyl-ring-one" />
            <div className="vinyl-ring vinyl-ring-two" />
            <div className="vinyl-label">
              <SignalMark />
              <b>signal</b>
              <span>play what fits</span>
            </div>
          </div>
          <p>09 traits<br />72 demo tracks<br />01 clear ranking</p>
        </div>
      </section>

      <section className="trust-strip" aria-label="Demo facts">
        <p><strong>Works right now</strong> No account needed</p>
        <p><strong>Clear by design</strong> Every match is explained</p>
        <p><strong>Safe to explore</strong> No login and no tracking</p>
      </section>

      <section className="workspace" id="try-it">
        <div className="section-intro">
          <p className="eyebrow"><span /> Try the engine</p>
          <h2>What do you want to hear?</h2>
          <p>This public demo uses a made-up catalog, so it is fast, private, and always ready.</p>
        </div>
        <SignalApp />
      </section>

      <section className="method" id="method">
        <div>
          <p className="eyebrow"><span /> Under the hood</p>
          <h2>Small enough to understand.<br />Useful enough to explore.</h2>
        </div>
        <ol>
          <li><span>01</span><div><strong>Turn sound into numbers</strong><p>Each track becomes a profile across tempo, energy, mood, danceability, and five more traits.</p></div></li>
          <li><span>02</span><div><strong>Compare the shape</strong><p>The engine normalizes every trait and uses a weighted distance to compare like with like.</p></div></li>
          <li><span>03</span><div><strong>Show the reason</strong><p>Results include the closest traits, not a mystery score with no context.</p></div></li>
        </ol>
      </section>

      <section className="disclosure">
        <SignalMark />
        <div>
          <p className="eyebrow">A note on the demo</p>
          <h2>Built around the API reality, not around it.</h2>
          <p>
            Spotify limits audio-feature access for most new developer apps, so this hosted version
            uses a deterministic 72-track demo catalog. The ranking logic is real and fully testable.
            The names and feature data are synthetic, and the scores are not claims about listener satisfaction.
          </p>
          <a href="https://developer.spotify.com/documentation/web-api/concepts/quota-modes" target="_blank" rel="noreferrer">
            Read Spotify&apos;s access rules <span aria-hidden="true">↗</span>
          </a>
        </div>
      </section>

      <footer>
        <a className="brand" href="#top"><SignalMark compact /><span>Signal</span></a>
        <p>Designed and built by Rohan Singh</p>
        <a href="https://github.com/RohanSi4/spotifyrecommender" target="_blank" rel="noreferrer">View the code ↗</a>
      </footer>
    </main>
  );
}
