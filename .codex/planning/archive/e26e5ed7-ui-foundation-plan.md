# UI Foundation

1. **Theme: dark, glassy visuals**
   - Background: full-screen clouds of color that drift slowly and shift hues while staying dark enough for icons to stand out.
   - Use images from `assets/` as backdrops, with fallbacks when assets fail to load.
   - Panels: frosted-glass surfaces with colored borders and subtle shadows for readability over illustrated backgrounds.
   - Headers: bold titles, small icons (close "X", status dots), accent highlights.
   - Text: modern sans-serif in light gray or white.
   - Palette: charcoal or navy backgrounds with high-contrast white text and consistent accent colors.
   - Buttons: rounded pills with gradients or solid accents; hover slightly scales and brightens.
   - Inputs: rounded fields with faint borders and blurred backgrounds.
2. Start the game in a 16:9 window (e.g., 1280×720) so desktop and phone builds behave consistently.
3. **Menus**
   - Build main menu with *New Run*, *Load Run*, *Edit Player*, *Options*, *Quit*.
   - Arrange options in a 2×3 high-contrast grid of large Lucide icons with clear labels, including a **Give Feedback** button.
   - Anchor the grid near the bottom edge with generous spacing for touch targets.
   - Reserve space for a central banner showcasing events and a top bar with player avatar, name, and currencies.
   - Cluster quick-access icons (notifications, mail, settings) in corners without overlapping main content.
     - Option stubs:
     - *New Run* begins the run setup flow.
        - Present a party picker for four owned characters plus the player.
        - If fewer than four characters are owned, allow starting with one to five party members; the player is always included.
        - After selection, display the floor map.
        - Allow entering a single unthemed room and returning to the map.
      - *Load Run* lists save slots.
      - *Edit Player* opens customization.
       - Offer Type A (Masculine), Type B (Feminine), and Type C (Androgynous) body types with selectable hair styles, colors, and accessories.
       - Present a 100-point stat pool; each point grants +1% to a chosen stat.
       - Clamp allocations so the total never exceeds the available points.
       - Spending 100 of each non-Generic damage type's 4★ upgrade item (Light, Dark, Wind, Lightning, Fire, Ice) buys one extra point; players must buy or craft these items before they can be spent.
      - Attempting to spend bonus points without sufficient 4★ items shows a warning and prevents confirmation.
      - Confirmation stays disabled until all available points—including any bonus points—are allocated.
   - Build the interface with web components (e.g., Svelte) and ensure keyboard and mouse navigation.
   - Provide a centralized scaling helper so menus keep their intended size across desktop and mobile viewports.
4. **Options submenu**
   - Sound-effects volume.
   - Music volume.
   - Toggle stat-screen pause behaviour.
   - Sliders clamp values within valid bounds and save immediately.
   - Lives in the frontend UI package and is invoked from the main menu.
5. Code structure:
   - Create a `ui/` package with modules for menus, options, and widgets.
   - Use a base `MenuScreen` class that handles navigation and animation hooks.
6. **Audio system**
   - A global `AudioManager` plays music and sound effects loaded via the asset pipeline.
   - Supports cross-fading tracks, volume sliders, and pausing via the Options menu.
   - Tests must play real browser audio to verify playback.
