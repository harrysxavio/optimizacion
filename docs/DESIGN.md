# Design System: Slotting Technical Control Tower

## 1. Visual Theme & Atmosphere

The technical UI uses an operational logistics aesthetic: dense enough for analysts, calm enough for long inspection sessions, and visually aligned with a warehouse control-tower workflow. The design should feel structured, factual, and purposeful rather than flashy.

## 2. Color Palette & Roles

| Name | Hex | Role |
|---|---:|---|
| Yard Concrete | `#f4f7f8` | Main app background. |
| Panel White | `#ffffff` | KPI cards, tables, chart containers. |
| Conveyor Ink | `#172022` | Primary text and headings. |
| Muted Steel | `#566769` | Captions, labels, secondary metadata. |
| Control Teal | `#2f6f73` | Left rail accents and operational emphasis. |
| Grid Line | `#d7e0df` | Borders around panels and data surfaces. |

## 3. Typography Rules

- **Headings**: Streamlit default sans-serif, semibold/bold, concise labels.
- **Body**: Streamlit default sans-serif, regular weight, compact explanatory copy.
- **Numerals/KPIs**: Use Streamlit metric styling; keep values short and scannable.
- **Command snippets**: Monospace code blocks for exact prerequisite commands.

## 4. Component Stylings

- **KPI cards**: White panels, subtle radius, thin grid border, teal left accent, low shadow.
- **Tables**: Full-width dataframes with visible borders and compact previews.
- **Charts**: Native Streamlit charts only in Phase 1.5; avoid heavy visualization dependencies.
- **Warnings/Notes**: Use Streamlit info/warning components for missing files and non-prescriptive scoring caveats.

## 5. Spacing & Layout

- **Density**: Prefer compact analytical layouts over marketing-style whitespace.
- **Grid**: Five KPI cards across desktop; two-column chart/table inspection below.
- **Responsive behavior**: Rely on Streamlit columns and full-width dataframes to collapse safely on narrower viewports.

## 6. Depth & Elevation

- **Cards**: Low elevation only (`rgba(23, 32, 34, 0.06)`) to separate panels without visual noise.
- **Layering**: No modals or overlays in Phase 1.5.

## 7. Motion & Animation

- No custom motion. This is a technical inspection surface; stability and readability take priority.
