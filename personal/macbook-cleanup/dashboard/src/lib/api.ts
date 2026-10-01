const fragment = new URLSearchParams(location.hash.slice(1));
const token = fragment.get("token") || location.hash.slice(1);
export const offline = Boolean(window.__MACBOOK_REPORT__);
export async function request<T>(path: string, body?: unknown): Promise<T> {
  if (offline)
    throw new Error(
      "Open the local review session to confirm cleanup. This saved report cannot delete files.",
    );
  const response = await fetch(`/api/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const value = await response.json();
  if (!response.ok)
    throw new Error(
      value.error || "The local operation could not be completed.",
    );
  return value;
}
