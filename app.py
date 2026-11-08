import streamlit as st
from research_team import Budget, Trace, CorpusSearch, Config, run

st.set_page_config(page_title="Slate Research Team", page_icon="🔎")
st.title("🔎 Slate Research Team")
st.caption("A multi-agent research pipeline: plan, search, verify with 2+ independent sources, write a cited report.")

EXAMPLES = ["How does an eight-cavity magnetron operate and when was it developed?",
            "How is a reflex klystron tuned electronically?",
            "What is a reflex klystron and when was the magnetron developed?",
            "What is the price of a magnetron in rupees?"]
choice = st.selectbox("Try an example", EXAMPLES)
question = st.text_input("Or type your own question", value=choice)
c1, c2 = st.columns(2)
max_searches = c1.slider("Search budget", 1, 10, 5)
break_search = c2.checkbox("Simulate search failure on 'magnetron'")

if st.button("Run research"):
    backend = CorpusSearch.from_file("data/corpus.json", fail_on=("magnetron",) if break_search else ())
    rep = run(question, backend, Budget(max_searches=max_searches), Trace(),
              Config(blocked=("forum.spam.example",)), sleep=lambda x: None)
    st.markdown(rep.markdown)
    st.info(f"Budget used: {rep.budget}")
    with st.expander("Trace log (every step the agents took)"):
        for e in rep.trace.events:
            st.json(e, expanded=False)
