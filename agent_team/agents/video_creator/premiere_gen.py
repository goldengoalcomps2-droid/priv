"""
Premiere Pro Project Generator - Converts a VideoBlueprint into
an Adobe Premiere Pro compatible XML project file (FCP XML format).

Generates:
- Sequence with correct resolution, fps, duration
- Video track with scene markers and clip placeholders
- Audio track with transcript markers
- Bins organised by scene
- Title/text overlay clips
"""

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring, indent


class PremiereProjectGen:
    """Generate Premiere Pro compatible XML project from a VideoBlueprint."""

    def generate(self, blueprint, output_dir: str = None) -> str:
        """Generate a Final Cut Pro XML (importable by Premiere Pro)."""
        bp = blueprint
        output_dir = Path(output_dir or ".")
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_title = bp.title[:40].replace(' ', '_').replace('/', '-')
        xml_path = output_dir / f"premiere_{safe_title}.xml"

        try:
            res_w, res_h = bp.resolution.split("x")
            res_w, res_h = int(res_w), int(res_h)
        except:
            res_w, res_h = 1920, 1080

        fps = int(bp.fps) if bp.fps else 30
        total_frames = int(bp.duration_seconds * fps)

        # Build XML
        xmeml = Element("xmeml", version="5")
        project = SubElement(xmeml, "project")
        SubElement(project, "name").text = bp.title

        children = SubElement(project, "children")

        # Main sequence
        sequence = SubElement(children, "sequence")
        SubElement(sequence, "name").text = f"{bp.title} - Main Edit"
        SubElement(sequence, "duration").text = str(total_frames)

        rate = SubElement(sequence, "rate")
        SubElement(rate, "timebase").text = str(fps)
        SubElement(rate, "ntsc").text = "FALSE"

        # Timecode
        tc = SubElement(sequence, "timecode")
        tc_rate = SubElement(tc, "rate")
        SubElement(tc_rate, "timebase").text = str(fps)
        SubElement(tc, "string").text = "00:00:00:00"
        SubElement(tc, "frame").text = "0"

        # Media
        media = SubElement(sequence, "media")

        # Video track
        video = SubElement(media, "video")
        vformat = SubElement(video, "format")
        sc = SubElement(vformat, "samplecharacteristics")
        SubElement(sc, "width").text = str(res_w)
        SubElement(sc, "height").text = str(res_h)
        sc_rate = SubElement(sc, "rate")
        SubElement(sc_rate, "timebase").text = str(fps)

        # Create video track with scene clips
        track = SubElement(video, "track")

        for i, scene_data in enumerate(bp.scenes):
            start_frame = int(scene_data.get("start", 0) * fps)
            end_frame = int(scene_data.get("end", 0) * fps)
            duration = end_frame - start_frame
            desc = scene_data.get("description", f"Scene {i+1}")

            clip = SubElement(track, "clipitem", id=f"scene_{i+1}")
            SubElement(clip, "name").text = f"Scene {i+1}: {desc[:50]}"
            SubElement(clip, "duration").text = str(duration)

            clip_rate = SubElement(clip, "rate")
            SubElement(clip_rate, "timebase").text = str(fps)

            SubElement(clip, "start").text = str(start_frame)
            SubElement(clip, "end").text = str(end_frame)
            SubElement(clip, "in").text = "0"
            SubElement(clip, "out").text = str(duration)

            # Add marker with description
            marker = SubElement(clip, "marker")
            SubElement(marker, "name").text = f"Scene {i+1}"
            SubElement(marker, "comment").text = desc[:200]
            SubElement(marker, "in").text = "0"

        # Title/text overlay track
        title_track = SubElement(video, "track")
        for i, scene_data in enumerate(bp.scenes):
            start_frame = int(scene_data.get("start", 0) * fps)
            end_frame = min(start_frame + fps * 3, int(scene_data.get("end", 0) * fps))
            desc = scene_data.get("description", "")[:40]

            gen_clip = SubElement(title_track, "generatoritem", id=f"title_{i+1}")
            SubElement(gen_clip, "name").text = f"Title: {desc}"
            SubElement(gen_clip, "duration").text = str(end_frame - start_frame)
            SubElement(gen_clip, "start").text = str(start_frame)
            SubElement(gen_clip, "end").text = str(end_frame)

            effect = SubElement(gen_clip, "effect")
            SubElement(effect, "name").text = "Text"
            SubElement(effect, "effectid").text = "Text"
            SubElement(effect, "effecttype").text = "generator"

            param = SubElement(effect, "parameter")
            SubElement(param, "parameterid").text = "str"
            SubElement(param, "name").text = "Text"
            SubElement(param, "value").text = desc

        # Audio track with transcript markers
        audio = SubElement(media, "audio")
        audio_track = SubElement(audio, "track")

        if bp.transcript_segments:
            for j, seg in enumerate(bp.transcript_segments[:100]):
                start_f = int(seg.get("start", 0) * fps)
                end_f = int(seg.get("end", 0) * fps)
                text = seg.get("text", "")

                a_clip = SubElement(audio_track, "clipitem", id=f"audio_seg_{j}")
                SubElement(a_clip, "name").text = text[:50]
                SubElement(a_clip, "start").text = str(start_f)
                SubElement(a_clip, "end").text = str(end_f)
                SubElement(a_clip, "duration").text = str(end_f - start_f)

                marker = SubElement(a_clip, "marker")
                SubElement(marker, "name").text = text[:30]
                SubElement(marker, "comment").text = text
                SubElement(marker, "in").text = "0"

        # Sequence markers for overall structure
        for i, scene_data in enumerate(bp.scenes):
            marker = SubElement(sequence, "marker")
            SubElement(marker, "name").text = f"Scene {i+1}"
            SubElement(marker, "comment").text = scene_data.get("description", "")[:200]
            SubElement(marker, "in").text = str(int(scene_data.get("start", 0) * fps))

        # Pretty print
        indent(xmeml, space="  ")
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n'
        xml_content += tostring(xmeml, encoding="unicode")

        xml_path.write_text(xml_content)

        return str(xml_path)
