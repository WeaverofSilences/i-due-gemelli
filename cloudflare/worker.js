/**
 * worker.js — Raccoglie i voti espliciti per il Gemello B.
 *
 * Due endpoint:
 *   POST /vote     -> incrementa il contatore di oggi. Chiamato dal sito.
 *   GET  /counts    -> ritorna il contatore corrente e lo azzera.
 *                      Chiamato una volta al giorno dalla GitHub Action,
 *                      con un token segreto — non e' un endpoint pubblico.
 *
 * Richiede un KV namespace collegato con il binding "VOTES".
 * Nessun altro dato viene raccolto: nessun indirizzo IP, nessun cookie,
 * nessun identificativo del visitatore. Solo un conteggio.
 */

const COUNTER_KEY = "pending_votes";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    if (url.pathname === "/vote" && request.method === "POST") {
      const current = parseInt((await env.VOTES.get(COUNTER_KEY)) || "0", 10);
      await env.VOTES.put(COUNTER_KEY, String(current + 1));
      return new Response(JSON.stringify({ ok: true }), {
        headers: { "Content-Type": "application/json", ...corsHeaders() },
      });
    }

    if (url.pathname === "/counts" && request.method === "GET") {
      const auth = request.headers.get("Authorization") || "";
      const expected = `Bearer ${env.READ_SECRET}`;
      if (auth !== expected) {
        return new Response("non autorizzato", { status: 401 });
      }
      const current = parseInt((await env.VOTES.get(COUNTER_KEY)) || "0", 10);
      await env.VOTES.put(COUNTER_KEY, "0"); // azzera dopo la lettura
      return new Response(JSON.stringify({ votes: current }), {
        headers: { "Content-Type": "application/json", ...corsHeaders() },
      });
    }

    return new Response("not found", { status: 404 });
  },
};
