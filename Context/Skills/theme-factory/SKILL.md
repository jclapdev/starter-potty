---
name: theme-factory
description: Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.
license: Complete terms in LICENSE.txt
---


# Theme Factory Skill

This skill provides a curated collection of professional font and color themes themes, each with carefully selected color palettes and font pairings. Once a theme is chosen, it can be applied to any artifact.

## Purpose

To apply consistent, professional styling to presentation slide decks, use this skill. Each theme includes:
- A cohesive color palette with hex codes
- Complementary font pairings for headers and body text
- A distinct visual identity suitable for different contexts and audiences

## Usage Instructions

To apply styling to a slide deck or other artifact:

1. **Show the theme showcase**: Display the `theme-showcase.pdf` file to allow users to see all available themes visually. Do not make any modifications to it; simply show the file for viewing.
2. **Ask for their choice**: Ask which theme to apply to the deck
3. **Wait for selection**: Get explicit confirmation about the chosen theme
4. **Apply the theme**: Once a theme has been chosen, apply the selected theme's colors and fonts to the deck/artifact

## Themes Available

The following 10 themes are available, each showcased in `theme-showcase.pdf`:

1. **[[Context/Skills/theme-factory/themes/ocean-depths.md|Ocean Depths]]** - Professional and calming maritime theme
2. **[[Context/Skills/theme-factory/themes/sunset-boulevard.md|Sunset Boulevard]]** - Warm and vibrant sunset colors
3. **[[Context/Skills/theme-factory/themes/forest-canopy.md|Forest Canopy]]** - Natural and grounded earth tones
4. **[[Context/Skills/theme-factory/themes/modern-minimalist.md|Modern Minimalist]]** - Clean and contemporary grayscale
5. **[[Context/Skills/theme-factory/themes/golden-hour.md|Golden Hour]]** - Rich and warm autumnal palette
6. **[[Context/Skills/theme-factory/themes/arctic-frost.md|Arctic Frost]]** - Cool and crisp winter-inspired theme
7. **[[Context/Skills/theme-factory/themes/desert-rose.md|Desert Rose]]** - Soft and sophisticated dusty tones
8. **[[Context/Skills/theme-factory/themes/tech-innovation.md|Tech Innovation]]** - Bold and modern tech aesthetic
9. **[[Context/Skills/theme-factory/themes/botanical-garden.md|Botanical Garden]]** - Fresh and organic garden colors
10. **[[Context/Skills/theme-factory/themes/midnight-galaxy.md|Midnight Galaxy]]** - Dramatic and cosmic deep tones

## Theme Details

Each theme is defined in the `themes/` directory with complete specifications including:
- Cohesive color palette with hex codes
- Complementary font pairings for headers and body text
- Distinct visual identity suitable for different contexts and audiences

## Application Process

After a preferred theme is selected:
1. Read the corresponding theme file from the `themes/` directory
2. Apply the specified colors and fonts consistently throughout the deck
3. Ensure proper contrast and readability
4. Maintain the theme's visual identity across all slides

## Describing Changes During Design Work

This rule moved here from `base-rules.md` because it only matters during visual work. When iterating on visual or design output (themes, layouts, UI), describe every change in outcome terms, what it will look like, never in implementation terms. "H3 headings will be pink" works. "Setting `--h3-color` to `#FF5879`" does not; the user cannot see CSS property names on a screen. This applies to every change description in a design session, not just the first one. Technical specs belong in the file, not in the explanation.

## Create your Own Theme

To handle cases where none of the existing themes work for an artifact, create a custom theme. Based on provided inputs, generate a new theme similar to the ones above. Give the theme a similar name describing what the font/color combinations represent. Use any basic description provided to choose appropriate colors/fonts. After generating the theme, show it for review and verification. Following that, apply the theme as described above.
