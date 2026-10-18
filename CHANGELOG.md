# Changelog

## 0.0.2

- Shape tab: only the settings the chosen mode uses are shown. Ellipsoid shows the axes,
  Contact binary the lobes, the spinning modes the gravity and period (plus the energy
  branch for Spinning uniform, and the axes for Spinning × ellipsoid). Highlands and
  lowlands are always there.
- Gravity is also on the Body tab, since it goes into the config for every mode.

## 0.0.1

First version, forked from Terra Studio 0.1.5.

- Shape: the body's shape comes from VertexHeightOblateAdvanced, with all five of its modes:
  Ellipsoid (`CustomEllipsoid`), Contact binary (`ContactBinary`), Spinning point mass
  (`PointEquipotential`), Spinning uniform (`UniformEquipotential`, low and high energy
  branch) and Spinning × ellipsoid (`Blend`). It is a port of the mod's own maths, with
  its limits, and it matches the mod to within 0.0000001 × the radius. The Shape tab shows
  the size in km.
- The height map holds only the detail; the shape is added in game by the mod.
- Noise, craters and placed features follow the real surface: craters are spread evenly
  per km² and keep their size in km on the tips of a long body.
- Live preview and preview sheet: the body is drawn in 3D with its real outline, its
  relief and shadows (a new Shadows switch). The mouse shows the altitude and the distance
  from the centre, and features can be placed on the body.
- Rock on steep slopes and the normal map use the real surface.
- Kopernicus config: the VertexHeightOblateAdvanced node, plus Properties with the radius,
  the gravity, the rotation period (spinning modes) and time warp heights above the
  highest point.
- Build info and log: the shape, the distance of the surface from the centre and the
  highest point above the radius.
- Asteroid-sized sliders (metres and fractions of a km), asteroid colour palettes and
  randomizers, domes instead of volcanoes, grooves instead of cracks.
- Removed from Terra Studio: the ocean, rivers, the Scatterer atmosphere, the climate
  colours and the In game view.
- Five example presets: Potato, Peanut, SpinningTop, Shard, IceFragment.
