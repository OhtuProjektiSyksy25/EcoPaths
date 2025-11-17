import { normalizeCoords } from "../../src/utils/coordsNormalizer";

describe("normalizeCoords", () => {
	it("returns null for null/undefined/invalid inputs", () => {
		expect(normalizeCoords(undefined)).toBeNull();
		expect(normalizeCoords(null)).toBeNull();
		expect(normalizeCoords(false)).toBeNull();
		// object without coordinates
		expect(normalizeCoords({})).toBeNull();
		// coordinates not an array
		expect(normalizeCoords({ coordinates: "not an array" })).toBeNull();
	});

	it("accepts raw coordinate arrays and wraps them as Point", () => {
		const arr = [24.94, 60.17];
		expect(normalizeCoords(arr)).toEqual({ type: "Point", coordinates: arr });
	});

	it("accepts GeoJSON Point geometry unchanged (type preserved)", () => {
		const geom = { type: "Point", coordinates: [13.4, 52.5] };
		expect(normalizeCoords(geom)).toEqual(geom);
	});

	it("accepts legacy shape with coordinates and infers Point type", () => {
		const legacy = { coordinates: [13.41, 52.51] };
		expect(normalizeCoords(legacy)).toEqual({ type: "Point", coordinates: legacy.coordinates });
	});

	it("returns null for invalid coordinate arrays (NaN, non-numeric, too short)", () => {
		expect(normalizeCoords([NaN, 50])).toBeNull();
		expect(normalizeCoords([13.4, "x" as any])).toBeNull();
		expect(normalizeCoords([13.4])).toBeNull();
	});
});
