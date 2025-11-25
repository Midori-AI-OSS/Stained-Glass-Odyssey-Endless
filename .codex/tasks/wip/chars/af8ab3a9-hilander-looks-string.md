# Add Looks String to Hilander Character

Suggested looks string (added after reviewing the provided photos). This block is a ready-to-copy triple-quoted string you can paste into `backend/plugins/characters/hilander.py` directly after `summarized_about` and before `char_type`.

## Description
Add a `looks` field to the Hilander character class (`backend/plugins/characters/hilander.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

## Recommended `looks` value
Copy the following into `hilander.py` as:

```py
looks = """
	Hilander reads as a comfortably large, lived-in human: an estimated ~6'0" frame (visual estimate), broad through the shoulders with a solid, relaxed torso and a tendency to carry weight low. He is solid more than sculpted—soft edges rather than sharp planes—with forearms that show light freckles and the faint patina of everyday use. When he stands he often shifts his weight onto one hip; when leaning on a porch post or railing he folds his arms or crosses them into a compact, protective silhouette rather than the erect posture of a trained athlete.

	His face is softly rounded with a jaw softened by light stubble and the casual shadow of a beard in some photos. The nose reads straight and slightly wide; the mouth usually rests neutral or in the barest, easy smile that makes his whole expression approachable. Skin is fair with freckles apparent on the forearms and occasionally across the nose in certain lighting. He commonly wears thin metal-rimmed glasses—simple, utilitarian frames that sit low on the bridge and give his gaze a quiet, practical focus. When glasses are absent his eyes look calm and unhurried.

	Hair is a defining element: very long, thick, and wavy, falling well past the shoulders in loose, natural waves. The base color is dark brown to deep chestnut with heavy streaking of gray and silver, creating a salt-and-pepper cascade that lightens into broad silver ribbons in bright light. Texture is slightly coarse with a natural frizz toward the ends; he sometimes pulls it back into a loose knot or ponytail, sometimes lets it tumble free. The part is soft and near-center, with stray wisps that frame the face and soften the overall silhouette.

	Clothing choices are casual and durable: faded graphic tees or plain muted shirts (black and earth tones recur), worn denim—cutoff shorts in summer and relaxed jeans otherwise—and comfortable shoes. Accessories are pragmatic: thin glasses, occasional over-ear headphones often seen around the neck or on the head, and simple hair clips when he ties his hair back. A cigarette appears in several photos as a recurring prop, held casually between two fingers; it contributes to the lived-in, slightly weathered atmosphere of many outdoor shots.

	Hands are medium-to-large and show mild callus and visible veins; nails are short and unadorned. He interacts with pets—usually cats—with immediate tenderness: cradling, supporting weight with open hands, thumbs rubbing chins. These small gestures loosen his posture and reveal a softer, companionable side that contrasts with the otherwise low-key exterior. No prominent tattoos or flashy jewelry are visible; when jewelry appears it is minimal and functional—an understated ring or thin ear stud.

	Movement and mannerisms are slow, deliberate, and unhurried. He often adopts a slightly slouched stance when seated or leaning and crosses his arms when stationary; his gestures are measured rather than abrupt. In indoor candid shots he frequently wears over-ear headphones and appears absorbed in music or a podcast. Outdoors, he tends to adopt a protective, almost watchful pose while remaining approachable—small crinkles at the eye and a ready ease with animals convey warmth.

	Signature visual vocabulary: long salt-and-pepper hair, thin metal glasses, faded tees and worn denim, over-ear headphones, the occasional cigarette, and the frequent company of cats. There are no magical or fantastical elements visible; his presentation is grounded, domestic, and deeply lived-in—a steady, approachable presence defined by soft stubble, silvered hair, practical clothing, and warm, small gestures.
"""
```

## Background
The repository is standardizing character descriptions by adding a `looks` string that provides detailed visual descriptions for each character. This supports future AI-powered features and provides rich context for character appearance.

## Reference Examples
See these files for the expected format:
- `backend/plugins/characters/luna.py` (lines 193-201)
- `backend/plugins/characters/ryne.py` (lines 24-54)
- `backend/plugins/characters/lady_light.py` (lines 16-24)
- `backend/plugins/characters/lady_darkness.py` (lines 16-25)

## Notes on placement and small edits
- Place the `looks` field in the `Hilander` dataclass immediately after the `summarized_about` attribute and before `char_type` to match the other character files' ordering.
- This is a cosmetic/documentation-only field — no game logic should be affected by adding it.

## Acceptance Criteria
- [ ] `looks` field added to the Hilander dataclass
- [ ] Content follows multi-paragraph format used in reference examples
- [ ] Triple-quoted string format used for multiline text
- [ ] Positioned after `summarized_about` and before `char_type`
- [ ] No changes to existing functionality

## Task Type
Documentation / Character Enhancement

## Priority
Low - Quality of life improvement

## Notes
- This is part of a batch update to add looks strings to all characters
