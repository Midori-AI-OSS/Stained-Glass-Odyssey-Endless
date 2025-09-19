# StarStorm Component

Renders a small constellation of orbiting element-colored orbs. Each orb has a fixed position, radius, and drift timing, and is rendered exactly once with a layered radial gradient that mixes its base color with the component tint. Slow transform/opacity animations are handled purely in CSS, so retinting the `StarStorm` background simply updates gradient stops instead of respawning DOM nodes. A reduced-motion branch swaps the animation for a static blended gradient so the background remains gently tinted without movement.
