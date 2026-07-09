import * as XLSX from "xlsx";

function normalizeHeader(value, index) {
	const text = String(value ?? "").trim();
	return text || `Колонка ${index + 1}`;
}

function uniqueColumns(headerRow) {
	const seen = {};
	return headerRow.map((cell, index) => {
		let name = normalizeHeader(cell, index);
		if (seen[name]) {
			seen[name] += 1;
			name = `${name} (${seen[name]})`;
		} else {
			seen[name] = 1;
		}
		return name;
	});
}

function rowHasData(row) {
	return row.some((cell) => String(cell ?? "").trim() !== "");
}

function cellToString(value) {
	if (value == null || value === "") return "";
	if (typeof value === "number") {
		if (Number.isInteger(value) && Math.abs(value) >= 1e10) {
			return value.toLocaleString("fullwide", { useGrouping: false });
		}
		return String(value);
	}
	return String(value).trim();
}

export async function parseExcelFile(file) {
	const buffer = await file.arrayBuffer();
	const workbook = XLSX.read(buffer, { type: "array", cellDates: false });
	const sheetName = workbook.SheetNames[0];
	const sheet = workbook.Sheets[sheetName];
	const matrix = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: "", raw: false });

	if (!matrix.length) {
		return { columns: [], rows: [], sheetName };
	}

	const headerRowIndex = matrix.findIndex((row) => {
		const filled = row.filter((cell) => cellToString(cell) !== "");
		return filled.length >= 2;
	});

	if (headerRowIndex === -1) {
		return { columns: [], rows: [], sheetName };
	}

	const columns = uniqueColumns(matrix[headerRowIndex]);
	const rows = matrix
		.slice(headerRowIndex + 1)
		.filter(rowHasData)
		.map((row) => {
			const record = {};
			columns.forEach((col, index) => {
				record[col] = cellToString(row[index]);
			});
			return record;
		});

	return { columns, rows, sheetName };
}

function buildFullName(row, mapping) {
	if (mapping.full_name) {
		return cellToString(row[mapping.full_name]);
	}
	if (Array.isArray(mapping.full_name_parts) && mapping.full_name_parts.length) {
		return mapping.full_name_parts
			.map((col) => cellToString(row[col]))
			.filter(Boolean)
			.join(" ");
	}
	return "";
}

function normalizeEmail(value) {
	return cellToString(value).toLowerCase().replace(/\s+/g, "");
}

function isValidEmail(email) {
	return /^[^\s@]+@[^\s@]+/.test(email);
}

export function mapRowsWithFields(rows, mapping) {
	if (!mapping.email && !mapping.full_name && !mapping.full_name_parts?.length) {
		return { valid: [], skipped: [] };
	}

	const valid = [];
	const skipped = [];

	for (let i = 0; i < rows.length; i++) {
		const row = rows[i];
		const email = mapping.email ? normalizeEmail(row[mapping.email]) : "";
		const full_name = buildFullName(row, mapping);
		const position = mapping.position
			? cellToString(row[mapping.position]) || null
			: null;

		if (!email || !full_name) {
			skipped.push({
				rowIndex: i + 1,
				reason: !email && !full_name
					? "нет email и ФИО"
					: !email
						? "нет email"
						: "нет ФИО",
				email,
				full_name,
			});
			continue;
		}

		if (!isValidEmail(email)) {
			skipped.push({
				rowIndex: i + 1,
				reason: "некорректный email",
				email,
				full_name,
			});
			continue;
		}

		valid.push({ email, full_name, position });
	}

	return { valid, skipped };
}

export function guessColumnMapping(columns) {
	const lower = columns.map((c) => ({ orig: c, low: c.toLowerCase() }));
	const find = (...words) => {
		const hit = lower.find(({ low }) => words.some((w) => low.includes(w)));
		return hit?.orig || "";
	};

	const full_name = find("фио", "fio", "ф.и.о", "full name", "fullname", "сотрудник", "full_name");
	const surname = find("фамилия", "surname", "lastname", "last name");
	const firstName = find("имя", "firstname", "first name", "name");
	const patronymic = find("отчество", "patronymic", "middle");

	const mapping = {
		email: find("email", "e-mail", "почта", "почт", "mail", "e_mail", "e mail"),
		full_name: full_name,
		position: find("должность", "долж", "position", "role", "title", "должн"),
	};

	if (!mapping.full_name && (surname || firstName)) {
		mapping.full_name_parts = [surname, firstName, patronymic].filter(Boolean);
		delete mapping.full_name;
	}

	return mapping;
}
