/**
 * После кадрирования скрина (crop в координатах исходного изображения) и добавления полей
 * пересчитывает area / area.actions в координатах нового изображения.
 *
 * @param {Record<string, unknown>|null|undefined} area
 * @param {{ x: number; y: number; w: number; h: number }} crop — прямоугольник в пикселях исходника
 * @param {{ left?: number; right?: number; top?: number; bottom?: number }} padding — поля вокруг кропа на новом холсте
 * @param {number} outW — ширина нового изображения
 * @param {number} outH — высота нового изображения
 */
export function transformAreaForCropPadding(area, crop, padding, outW, outH) {
	if (!area || typeof area !== "object") return area;
	const pl = Math.max(0, Math.round(Number(padding?.left) || 0));
	const pr = Math.max(0, Math.round(Number(padding?.right) || 0));
	const pt = Math.max(0, Math.round(Number(padding?.top) || 0));
	const pb = Math.max(0, Math.round(Number(padding?.bottom) || 0));
	const cx = Math.max(0, Math.round(crop.x));
	const cy = Math.max(0, Math.round(crop.y));
	const dx = pl - cx;
	const dy = pt - cy;

	const clamp = (r) => {
		let x = Math.round(Number(r.x) || 0) + dx;
		let y = Math.round(Number(r.y) || 0) + dy;
		let w = Math.max(1, Math.round(Number(r.width) || 0));
		let h = Math.max(1, Math.round(Number(r.height) || 0));
		x = Math.max(0, Math.min(x, outW - 1));
		y = Math.max(0, Math.min(y, outH - 1));
		if (x + w > outW) w = Math.max(1, outW - x);
		if (y + h > outH) h = Math.max(1, outH - y);
		return { ...r, x, y, width: w, height: h };
	};

	const metaKeys = [
		"metaText",
		"metaKeywords",
		"metaFontSize",
		"metaTextScale",
		"metaMatchMode",
		"metaPattern",
		"metaPatternPreset",
	];

	const pickMeta = (src) => {
		const o = {};
		for (const k of metaKeys) {
			if (k in src && src[k] != null) o[k] = src[k];
		}
		return o;
	};

	const out = { ...area };
	const rawActions = area.actions;
	if (Array.isArray(rawActions) && rawActions.length) {
		const next = rawActions.map((a) => {
			if (!a || typeof a !== "object") return a;
			const w = Number(a.width) || 0;
			const h = Number(a.height) || 0;
			if (w > 0 && h > 0) {
				return clamp({ ...a });
			}
			return { ...a };
		});
		out.actions = next;
		const first = next[0];
		if (first && (Number(first.width) || 0) > 0) {
			Object.assign(out, {
				x: first.x,
				y: first.y,
				width: first.width,
				height: first.height,
				...pickMeta(first),
			});
		}
		return out;
	}

	if ((Number(area.width) || 0) > 0 && (Number(area.height) || 0) > 0) {
		const r = clamp({
			x: Number(area.x) || 0,
			y: Number(area.y) || 0,
			width: Number(area.width) || 0,
			height: Number(area.height) || 0,
		});
		Object.assign(out, r, pickMeta(area));
	}

	return out;
}
