import os
import pandas as pd
import streamlit as st
import config, db, llm
from analyzers import scan_folder
from rag import VectorIndex, load_code_chunks, load_rules

st.set_page_config(page_title="Secure Code Review Assistant", layout="wide")
st.title("Secure Code Debugging and Review Assistant")
st.caption("Local LLM (Ollama) + RAG (FAISS) + deterministic rules. AI output is advisory; engineer review is required.")


@st.cache_resource(show_spinner="Building local indexes...")
def get_indexes():
    return VectorIndex(load_code_chunks(config.CODE_DIR)), VectorIndex(load_rules(config.RULES_FILE))


code_idx, rule_idx = get_indexes()
rules_by_id = {r["rule_id"]: r for r in rule_idx.items}

with st.sidebar:
    st.header("Knowledge base")
    st.write(f"Code chunks: **{len(code_idx.items)}**  \nGuideline rules: **{len(rule_idx.items)}**")
    up = st.file_uploader("Add a .c / .h file", type=["c", "h"])
    if up and st.button("Add & re-index"):
        open(os.path.join(config.CODE_DIR, up.name), "wb").write(up.getvalue())
        get_indexes.clear()
        st.rerun()
    st.write(f"Model: `{config.LLM_MODEL}`  \nEmbeddings: `{config.EMBED_MODEL}`")


def show_cites(code_hits, rule_hits):
    with st.expander("Retrieved evidence / citations"):
        for h in code_hits:
            st.markdown(f"**[{h['file']}:{h['start']}-{h['end']}]** (score {h['score']:.2f})")
            st.code(h["text"], language="c")
        for h in rule_hits:
            st.markdown(f"**[{h['rule_id']}]** {h['text']}")


tab1, tab2, tab3, tab4 = st.tabs(["Code Q&A", "Review scan", "Log / warning analysis", "Findings & export"])

with tab1:
    q = st.text_input("Ask about the code (e.g. 'Which function is vulnerable to buffer overflow?')")
    if st.button("Ask") and q:
        ch, rh = code_idx.search(q, config.TOP_K), rule_idx.search(q, 2)
        with st.spinner("Thinking locally..."):
            st.write(llm.ask(llm.build_prompt(q, ch, rh)))
        show_cites(ch, rh)

with tab2:
    if st.button("Run deterministic scan"):
        st.session_state["findings"] = scan_folder(config.CODE_DIR)
        st.session_state.pop("expl", None)
    fl = st.session_state.get("findings", [])
    if fl:
        st.dataframe(pd.DataFrame(fl), use_container_width=True)
        labels = [f"{i}: {f['file']}:{f['line']} [{f['rule']}] {f['title']}" for i, f in enumerate(fl)]
        sel = st.selectbox("Select a finding", labels)
        f = fl[int(sel.split(":")[0])]
        st.code(f["snippet"], language="c")
        if st.button("Explain with AI"):
            path = os.path.join(config.CODE_DIR, f["file"])
            lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
            s, e = max(0, f["line"] - 6), min(len(lines), f["line"] + 5)
            ctx = [{"file": f["file"], "start": s + 1, "end": e, "text": "\n".join(lines[s:e]), "score": 1.0}]
            rh = [rules_by_id[f["rule"]]] if f["rule"] in rules_by_id else []
            task = (f"Finding {f['rule']} at {f['file']}:{f['line']}: {f['title']}. Explain the root cause, "
                    f"the risk, and give a corrected code fix. Cite the rule.")
            with st.spinner("Generating..."):
                st.session_state["expl"] = (llm.ask(llm.build_prompt(task, ctx, rh)), ctx, rh)
        if "expl" in st.session_state:
            text, ctx, rh = st.session_state["expl"]
            st.markdown(text)
            show_cites(ctx, [dict(r) for r in rh])
            c1, c2 = st.columns(2)
            if c1.button("Accept finding"):
                db.save(f, text, "ACCEPTED"); st.success("Saved as ACCEPTED")
            if c2.button("Reject (false positive)"):
                db.save(f, text, "REJECTED"); st.warning("Saved as REJECTED")

with tab3:
    log = st.text_area("Paste compiler warning / static-analysis / runtime log", height=150,
                       placeholder="ecu_can.c:46: warning: implicit declaration of function 'gets'")
    if st.button("Analyse log") and log:
        ch, rh = code_idx.search(log, config.TOP_K), rule_idx.search(log, 2)
        with st.spinner("Analysing..."):
            st.write(llm.ask(llm.build_prompt("Interpret this log, give the likely root cause and fix:\n" + log, ch, rh)))
        show_cites(ch, rh)

with tab4:
    df = db.all_findings()
    if df.empty:
        st.info("No reviewed findings yet. Accept/reject findings in the Review scan tab.")
    else:
        a, b, c = st.columns(3)
        a.metric("Reviewed", len(df))
        b.metric("Accepted", int((df.status == "ACCEPTED").sum()))
        c.metric("Rejected", int((df.status == "REJECTED").sum()))
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.groupby("severity").size())
        st.download_button("Export CSV", df.to_csv(index=False), "findings.csv")
        st.download_button("Export JSON", df.to_json(orient="records", indent=2), "findings.json")
