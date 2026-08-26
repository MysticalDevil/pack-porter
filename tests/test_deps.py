from pack_porter.deps import DependencyResolver
from pack_porter.model import ResolvedMod


class FakeMr:
    def __init__(self, projects, versions):
        self.projects = projects  # {project_id: {"slug": ...}}
        self.versions = versions  # {slug: {"dependencies": [...]}}

    def get_project(self, pid):
        return self.projects.get(pid)

    def required_deps(self, meta):
        return [
            d.get("project_id")
            for d in meta.get("dependencies", [])
            if d.get("dependency_type") == "required"
        ]

    def resolve(self, slug, loader, mc):
        meta = self.versions.get(slug, {"dependencies": []})
        return ResolvedMod(filename=f"{slug}.jar", url=f"https://x/{slug}.jar", sha1=None, meta=meta)


def _root(project_id):
    return {"dependencies": [{"dependency_type": "required", "project_id": project_id}]}


def test_single_level():
    mr = FakeMr({"p1": {"slug": "dep-a"}}, {"dep-a": {"dependencies": []}})
    out = DependencyResolver(mr, set()).collect(_root("p1"), "fabric", "1.19.4")
    assert [s for s, _ in out] == ["dep-a"]


def test_transitive():
    mr = FakeMr(
        {"p1": {"slug": "a"}, "p2": {"slug": "b"}},
        {
            "a": {"dependencies": [{"dependency_type": "required", "project_id": "p2"}]},
            "b": {"dependencies": []},
        },
    )
    out = DependencyResolver(mr, set()).collect(_root("p1"), "fabric", "1.19.4")
    assert [s for s, _ in out] == ["a", "b"]


def test_cycle():
    mr = FakeMr(
        {"p1": {"slug": "a"}, "p2": {"slug": "b"}},
        {
            "a": {"dependencies": [{"dependency_type": "required", "project_id": "p2"}]},
            "b": {"dependencies": [{"dependency_type": "required", "project_id": "p1"}]},
        },
    )
    out = DependencyResolver(mr, set()).collect(_root("p1"), "fabric", "1.19.4")
    assert [s for s, _ in out] == ["a", "b"]


def test_skip_if_in_manifest():
    mr = FakeMr({"p1": {"slug": "a"}}, {"a": {"dependencies": []}})
    out = DependencyResolver(mr, {"a"}).collect(_root("p1"), "fabric", "1.19.4")
    assert out == []
