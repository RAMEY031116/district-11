# District 11 mobile update

Replace app.py and requirements.txt in the existing repository with these files. Keep db.py, calculations.py and your Streamlit secrets. Redeploy/reboot Streamlit after updating dependencies. No database migration is needed.

Changes: fixed bottom navigation on mobile; accessible native button shortcuts; pending debt opens Balance; individual payment shortcuts place that payment first; larger touch targets; stacked forms; compact expandable quick-add; clearer labels and less duplicated home-page content.

Validation: Python compilation and three Streamlit AppTest tests passed using fixture data. Tests cover four dashboard destinations, selected payment ordering, receipt confirmation, and the zero-debt state. No live database or deployed-device visual test was performed.

Run tests: python test_navigation.py

Alternative: apply district-11-mobile.patch with git apply.
