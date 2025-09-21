# ElementOrbs Component

Renders a small constellation of orbiting element-colored orbs as a background effect. Each orb has a deterministic position, radius, and drift timing based on a unique identifier, ensuring consistent visuals between renders. The orbs are rendered exactly once with layered radial gradients that mix their base color with the component tint. 

Slow transform/opacity animations are handled purely in CSS using deterministic timing from the animation tokens system. Retinting the `ElementOrbs` background simply updates gradient stops instead of respawning DOM nodes. A reduced-motion branch swaps the animation for a static blended gradient so the background remains gently tinted without movement.

The component integrates with the animation tokens system to provide:
- Deterministic drift durations and delays based on orb IDs
- Proper animation speed scaling based on user preferences  
- Respect for granular motion settings (disableStarStorm/disableElementOrbs)
- Support for prefers-reduced-motion browser preference
