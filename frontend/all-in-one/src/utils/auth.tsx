export function getUserFromToken() {
  // Check both localStorage and sessionStorage
  let token = localStorage.getItem("access_token");
  let tokenSource = "localStorage";

  if (!token) {
    token = sessionStorage.getItem("access_token");
    tokenSource = "sessionStorage";
  }

  console.log(`[auth] access_token from ${tokenSource}:`, token ? `${token.substring(0, 50)}...` : 'null');

  if (!token) {
    console.log("[auth] No token found in localStorage or sessionStorage");
    return null;
  }

  try {
    const payloadBase64 = token.split(".")[1];
    const payloadDecoded = JSON.parse(atob(payloadBase64));

    console.log("[auth] Decoded JWT payload:", payloadDecoded);

    return {
      id: payloadDecoded.sub,
      role: payloadDecoded.role || "Unknown",
      department: payloadDecoded.departments?.[0] || "Unknown", // take first dept
      teams: payloadDecoded.teams || []
    };
  } catch (e) {
    console.error("[auth] Failed to decode JWT", e);
    return null;
  }
}
