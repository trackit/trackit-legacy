class TreeViewComponent extends React.Component {

    constructor() {
        super();
        this.isSelected = this.isSelected.bind(this);
    }

    setActive(filename) {
        this.props.selectFunc(filename);
    }

    isSelected(filename) {
        if (this.props.state.sourceElement.indexOf(filename) != -1 || this.props.state.destinationElement == filename)
            return true;
        return false;
    }

    isInTransfers(filename) {
        for (var i = 0; i < this.props.state.transfers.length; i++) {
            var tmp = this.props.state.transfers[i];
            if (tmp.source == filename || tmp.destination == filename)
                return true;
            }
        return false;
    }

    render() {
        let iconsStyle = {
            color: "#0088CC",
            fontSize: "18px",
        };

        let badgesStyle = {
            backgroundColor: "#0088CC",
            fontSize: "13px",
            margin: "0 5px"
        };

        const betterOnClickArea = {
            padding: "10px 0px"
        };

        const betterArrowClick = {
            padding: "6px"
        }

        if (this.props.colorCode) {
            iconsStyle.color = this.props.colorCode;
            badgesStyle.backgroundColor = this.props.colorCode;
        }

        const selectedBadge = <span className="badge" style={badgesStyle}>
            <i className="fa fa-check-square-o"></i>
            &nbsp;Selected</span>;
        const inTransfersBadge = <span className="badge" style={badgesStyle}>
            <i className="fa fa-list"></i>
            &nbsp;In transfers queue</span>;

        return (
            <div>
                {this.props.treeData.map((node, i) => {
                    const name = node.name;
                    const label = <span className="node" onClick={this.setActive.bind(this, name)} style={betterOnClickArea}>
                        <i className="fa fa-folder-open" style={iconsStyle}></i>&nbsp;{name}
                          {this.isSelected(name) && selectedBadge}
                          {this.isInTransfers(name) && inTransfersBadge}
                    </span>;
                    return (
                        <TreeView key={name + '|' + i} nodeLabel={label} defaultCollapsed={true} style={betterArrowClick}>
                            {node.children.map(children => {
                                const label2 = <span className="node" onClick={this.setActive.bind(this, children.name)} style={betterOnClickArea}>
                                    <i className={"fa " + getFileIconCode(children.name)} style={iconsStyle}></i>&nbsp;{children.name}
                                      {this.isSelected(children.name) && selectedBadge}
                                      {this.isInTransfers(children.name) && inTransfersBadge}
                                </span>;

                                return (
                                    <TreeView nodeLabel={label2} key={children.name} defaultCollapsed={true} style={betterArrowClick}>
                                        <div className="info">
                                            <strong>type</strong>: {children.type}</div>
                                        <div className="info">
                                            <strong>name</strong>: {children.name}</div>
                                        <div className="info">
                                            <strong>size</strong>: {bytesToSize(children.size)}</div>
                                    </TreeView>
                                );
                            })}
                        </TreeView>
                    );
                })}
            </div>
        );
    }
}

TreeViewComponent.propTypes = {
    treeData: React.PropTypes.array.isRequired,
    selectFunc: React.PropTypes.func,
    colorCode: React.PropTypes.string,
    state: React.PropTypes.object.isRequired,
};
