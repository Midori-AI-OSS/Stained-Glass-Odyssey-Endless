# Party UI

The party management interface uses a unified `CharacterEditor` inside `StatTabs` for both player and non‑player characters. The editor exposes sliders for HP, Attack, Defense, Crit Rate, and Crit Damage. Player edits persist via `/player/editor` while NPC tweaks remain local for previewing.

An `UpgradePanel` sits below the editor so any character can convert upgrade items into points and spend them on specific stats using the shared `/players/<id>/upgrade` and `/players/<id>/upgrade-stat` endpoints.

`StatTabs` no longer includes the old Effects tab; all characters share the same scrollable stat view and slider controls.

## PartyPicker layout

- The `PartyPicker` overlay keeps the glass panel pinned; `MenuPanel` is rendered with `scrollable={false}` so the outer modal no
  longer scrolls. Only the left roster column scrolls.
- `PartyRoster` locks its container height to the panel viewport and exposes an internal scroll region that preserves the Party
  header and sort controls.
- Gradient fades appear at the top and bottom of the roster list when additional heroes are available. The fades disappear when
  the list fits without scrolling to hint at the available motion affordance without introducing extra buttons.
