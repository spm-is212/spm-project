export function getUserFromToken() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;

  try {
    const payloadBase64 = token.split(".")[1];
    const payloadDecoded = JSON.parse(atob(payloadBase64));

    console.log("Decoded JWT payload:", payloadDecoded);

    return {
      id: payloadDecoded.sub,
      role: payloadDecoded.role || "Unknown",
      department: payloadDecoded.departments?.[0] || "Unknown", // take first dept
      teams: payloadDecoded.teams || []
    };
  } catch (e) {
    console.error("Failed to decode JWT", e);
    return null;
  }
}
