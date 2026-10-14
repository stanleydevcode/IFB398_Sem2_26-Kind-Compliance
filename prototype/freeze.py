# Saves every page as a static HTML file in ./build
from flask_frozen import Freezer

import data
from app import app

app.config["FREEZER_DESTINATION"] = "build"
app.config["FREEZER_RELATIVE_URLS"] = True
app.config["FREEZER_REDIRECT_POLICY"] = "ignore"
freezer = Freezer(app)


@freezer.register_generator
def all_pages():
    yield "sign_in", {}
    for role in data.ROLES:
        for ep, _ in data.NAV[role]:
            yield ep, {"role": role}
        yield "report_incident", {"role": role}
        for p in data.participants_for(role):
            yield "participant", {"role": role, "slug": p["slug"]}
        if role != "staff":
            for doc in data.policy_documents():
                yield "document", {"role": role, "slug": doc["slug"]}
            yield "my_compliance", {"role": role}
            for w in data.WORKERS:
                yield "worker", {"role": role, "slug": w["slug"]}
                if w["login"] == "staff":
                    yield "worker_preview", {"role": role, "slug": w["slug"]}
            for c in data.cases_for(role):
                yield "case", {"role": role, "slug": c["slug"]}


if __name__ == "__main__":
    freezer.freeze()
    print("Built to ./build")
