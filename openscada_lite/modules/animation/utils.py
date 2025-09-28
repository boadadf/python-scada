class Utils:
    @staticmethod
    def compute_gsap_cfg(cfg, value):
        t = cfg.get("type")
        duration = cfg.get("duration", 0.5)
        # Convert value to float if possible
        try:
            value_num = float(value)
        except (TypeError, ValueError):
            value_num = 0

        if t == "height_y":
            maxH = cfg["maxHeight"]
            baseY = cfg["baseY"]
            newH = min(max(value_num, 0), 100)/100 * maxH
            newY = baseY - newH
            return {"attr": {"height": newH, "y": newY}, "duration": duration}
        elif t == "fill_color":
            minV = cfg["minValue"]
            maxV = cfg["maxValue"]
            v = min(max(value_num, minV), maxV)
            red = int((v - minV)/(maxV-minV)*255)
            return {"attr": {"fill": f"rgb({red},0,0)"}, "duration": duration}
        elif t == "fill_toggle":
            value_map = cfg.get("map")
            if value_map and isinstance(value_map, dict):
                # If value matches an enum in the map
                color = value_map.get(str(value), cfg.get("offColor", "gray"))
            else:
                # Fallback: handle as boolean
                color = cfg.get("onColor") if bool(value) else cfg.get("offColor")
            return {"attr": {"fill": color}, "duration": duration}
        elif t == "text":
            # Use GSAP TextPlugin
            return {"text": str(value), "duration": duration}
        else:
            return {"attr": {}, "duration": duration}