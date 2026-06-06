const APP_TITLE = "SkillSnap";

export function isSystemNotificationSupported() {
	return typeof window !== "undefined" && "Notification" in window;
}

export function getSystemNotificationPermission() {
	if (!isSystemNotificationSupported()) return "unsupported";
	return Notification.permission;
}

export async function requestSystemNotificationPermission() {
	if (!isSystemNotificationSupported()) return "unsupported";
	if (Notification.permission === "granted") return "granted";
	if (Notification.permission === "denied") return "denied";

	try {
		return await Notification.requestPermission();
	} catch {
		return "denied";
	}
}

export function showSystemNotification({
	title,
	body,
	tag,
	trainingUuid,
	onClick,
}) {
	if (!isSystemNotificationSupported()) return null;
	if (Notification.permission !== "granted") return null;

	try {
		const notification = new Notification(title || APP_TITLE, {
			body: body || "",
			tag: tag || undefined,
			icon: "/favicon.png",
			badge: "/favicon.png",
			requireInteraction: false,
		});

		notification.onclick = (event) => {
			event.preventDefault();
			window.focus();
			if (trainingUuid) {
				const url = `/edit/${trainingUuid}`;
				if (window.location.pathname !== url) {
					window.location.href = url;
				}
			}
			onClick?.();
			notification.close();
		};

		setTimeout(() => notification.close(), 12000);

		return notification;
	} catch (error) {
		console.warn("System notification failed:", error);
		return null;
	}
}
