import maya.cmds as mc


class AnimOpsExportPrep(object):
    def __init__(self):
        self.skl_sel = []
        self.geo_sel = []
        self.final_sel = []

    def run(self):
        self._manage_namespaces()
        self._select_and_compile()

    def _manage_namespaces(self):
        """Handle namespaces: remove unwanted ones and merge with parent."""
        default_namespaces = ["UI", "shared"]
        namespaces = mc.namespaceInfo(lon=True)

        for ns in namespaces:
            if ns not in default_namespaces:
                mc.namespace(removeNamespace=ns, mergeNamespaceWithParent=True)

    def _select_and_compile(self):
        """Select SKL_lyr and GEO_lyr layers and compile them into a final selection list."""
        # Select SKL_lyr and gather connections
        if mc.objExists("SKL_lyr"):
            self.skl_sel = mc.listConnections("SKL_lyr") or []
            if self.skl_sel:
                self.skl_sel.pop(0)

        # Select GEO_lyr and gather connections
        if mc.objExists("GEO_lyr"):
            self.geo_sel = mc.listConnections("GEO_lyr") or []
            if self.geo_sel:
                self.geo_sel.pop(0)

        # Compile final selection
        self.final_sel.extend(self.geo_sel)
        self.final_sel.extend(self.skl_sel)

        if self.final_sel:
            mc.select(self.final_sel)


def main(*args):
    exporter = AnimOpsExportPrep()
    exporter.run()
