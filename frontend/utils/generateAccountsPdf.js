import pdfMake from "pdfmake/build/pdfmake";
import pdfFonts from "pdfmake/build/vfs_fonts";
import { formatAccountExpiresAt } from "./formatAccountExpiresAt.js";

pdfMake.vfs = pdfFonts.pdfMake?.vfs || pdfFonts.vfs;

export function downloadAccountsPdf(organizationName, accounts) {
	if (!accounts?.length) return;

	const date = new Date().toLocaleDateString("ru-RU", {
		day: "2-digit",
		month: "long",
		year: "numeric",
	});
	const ttlDays = accounts[0]?.ttl_days || 30;

	const docDefinition = {
		pageMargins: [40, 48, 40, 48],
		content: [
			{ text: "Учётные записи сотрудников", style: "title" },
			{
				text: organizationName || "Организация",
				style: "subtitle",
				margin: [0, 4, 0, 2],
			},
			{ text: `Дата формирования: ${date}`, style: "meta", margin: [0, 0, 0, 4] },
			{
				text: `Срок действия учётных записей: ${ttlDays} дн. (после истечения доступ удаляется автоматически)`,
				style: "meta",
				margin: [0, 0, 0, 20],
			},
			{
				table: {
					headerRows: 1,
					widths: ["*", "*", 90, 80],
					body: [
						[
							{ text: "ФИО", style: "tableHeader" },
							{ text: "Email (логин)", style: "tableHeader" },
							{ text: "Пароль", style: "tableHeader" },
							{ text: "До", style: "tableHeader" },
						],
						...accounts.map((acc) => [
							acc.full_name || "—",
							acc.email || "—",
							acc.temp_password || "—",
							formatAccountExpiresAt(acc.account_expires_at) || "—",
						]),
					],
				},
				layout: {
					fillColor: (rowIndex) => (rowIndex === 0 ? "#eef2ff" : rowIndex % 2 ? "#f8fafc" : null),
					hLineColor: () => "#e2e8f0",
					vLineColor: () => "#e2e8f0",
					paddingLeft: () => 8,
					paddingRight: () => 8,
					paddingTop: () => 6,
					paddingBottom: () => 6,
				},
			},
			{
				text: "Передайте каждому сотруднику его строку. По истечении срока учётная запись будет удалена.",
				style: "footer",
				margin: [0, 16, 0, 0],
			},
		],
		styles: {
			title: { fontSize: 18, bold: true, color: "#1e293b" },
			subtitle: { fontSize: 13, color: "#5064f7", bold: true },
			meta: { fontSize: 10, color: "#64748b" },
			tableHeader: { bold: true, fontSize: 10, color: "#334155" },
			footer: { fontSize: 9, color: "#64748b", italics: true },
		},
		defaultStyle: { font: "Roboto", fontSize: 10 },
	};

	const safeName = (organizationName || "organizaciya")
		.replace(/[^\wа-яА-ЯёЁ\s-]/gi, "")
		.trim()
		.replace(/\s+/g, "_")
		.slice(0, 40);

	pdfMake.createPdf(docDefinition).download(`uchetnye-zapisi_${safeName}.pdf`);
}
