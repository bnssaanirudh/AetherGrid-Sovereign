# Prompt 11 Handoff: Premium Public Landing Site

## Overview
A standalone, production-ready marketing site has been scaffolded at `website/`. This application is entirely decoupled from the heavy `frontend/` operator dashboard to maximize SEO, Core Web Vitals, and support static edge hosting.

## Architecture & Technology Stack
- **Framework**: Next.js 14 App Router configured for static HTML export (`output: "export"`).
- **Styling**: Tailwind CSS v4, initialized with a dark mode by default using deep slate and cyan accents.
- **Motion**: Framer Motion for scroll reveals, respecting `prefers-reduced-motion`.
- **Content Layer**: All site text, use cases, and feature claims are decoupled from React components and stored in `website/src/content/data.ts`. This ensures strict adherence to claim-discipline.

## Completed Components
- `Navbar`: Fixed header with backdrop blur and responsive mobile hamburger menu.
- `Hero`: Animated typography showcasing the primary value proposition.
- `LogoMarquee`: Infinite scroll displaying the actual open-source dependencies (e.g., PyTorch Geometric, PennyLane).
- `CapabilityGrid`: Binds directly to the verified capabilities of the AetherGrid repo. (Quantum VQC capabilities are explicitly tagged with a 'Research Preview' badge).
- `SplitSection`: Editorial layout juxtaposing infrastructure threats with the AetherGrid architectural solution.
- `UseCaseTabs`: Accessible, keyboard-navigable tabs demonstrating real-world scenarios.
- `EvidenceFeed`: Highlights verifiable artifacts like the STRIDE Threat Model and Q-HGT benchmark load profile.
- `ClosingCTA`: A call-to-action featuring an animated pipeline sequence representing the actual data flow.
- `Footer`: Links strictly pointing to verified repository assets and standard navigation.

## Testing & Quality Assurance
A comprehensive Playwright test suite (`website/tests/smoke.spec.ts`) was executed successfully. It guarantees:
1. The homepage mounts correctly with the Hero typography.
2. All anchor links resolve to valid, non-dead endpoints.
3. Interactive ARIA tabs (`UseCaseTabs`) function perfectly via DOM assertions.
4. The mobile menu expands and collapses responsively.

## Deployment Instructions
The static site can be generated at any time:
```bash
cd website
npm run build
```
The output will reside in `website/out/`, ready to be served statically via any standard node server, nginx, or bucket storage without requiring a Node.js runtime.

## Caveats / Placeholders
- **Domain Links**: URLs in `website/src/content/data.ts` currently use `https://aethergrid.ai` and should be updated to the production domain.
- **Evidence Links**: The `EvidenceFeed` uses GitHub Blob links back into the repository markdown files to fulfill the strict claim-discipline rule since a public blog does not yet exist.
