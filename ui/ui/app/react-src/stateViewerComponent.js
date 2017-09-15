class StateViewerComponent extends React.Component {

    constructor() {
        super();
        this.state = {
            sourceFull: null,
            destFull: null
        }
        this.clear = this.clear.bind(this);
        this.addTransfer = this.addTransfer.bind(this);
    }

    componentWillReceiveProps(nextProps) {
        if (nextProps.state.destinationElement) {
            var destInfos = findInMockData(nextProps.state.destinationElement);
            this.setState({destFull: destInfos});
        } else {
            this.setState({destFull: null});
        }
    }

    clear() {
        this.setState({sourceFull: null, destFull: null});
    }

    addTransfer() {
        this.clear();
        this.props.addTransferFunc();
    }

    getSourceRow(theSource) {

        const sourceBadgesStyle = {
            backgroundColor: "#FF9900",
            fontSize: "13px",
            margin: "3px 5px"
        };

        var sourceInfos = findInMockData(theSource);

        let sourceBadges = null;
        if (sourceInfos) {
            sourceBadges = <div>
                <span className="badge" style={sourceBadgesStyle}>Type : {sourceInfos.type}</span>

                {sourceInfos.children && <span className="badge" style={sourceBadgesStyle}>Contains files :
                    <i className="fa fa-check-circle"></i>
                </span>}
                {sourceInfos.size && <span className="badge" style={sourceBadgesStyle}>Size : {bytesToSize(sourceInfos.size)}
                </span>}

            </div>
        }

        return (
          <li key={theSource} className="list-group-item" style={{padding: "0px"}}>
            <h5>
                <i className="fa fa-arrow-circle-up" style={{
                    color: "#FF9900"
                }}></i>
                &nbsp;Source : {sourceInfos && !sourceInfos.children && <span>{theSource} {sourceBadges}</span>}
                {sourceInfos && sourceInfos.children && <span>
                    <i className="fa fa-times"></i>
                    Please select a file</span>}

            </h5>
          </li>


        );
    }

    render() {
        const arrowStyle = {
            display: "block",
            textAlign: "center",
            fontSize: "29px"
        };

        const destBadgesStyle = {
            backgroundColor: "#0088CC",
            fontSize: "13px",
            margin: "0 5px"
        };

        const infosStyle = {
            fontSize: "13px",
            marginLeft: "21px"
        };

        const noDestMessage = <span>
            No destination selected.
            <br/>
            <span style={infosStyle}>Destinations can only be buckets</span>
        </span>

        let destBadges = null;
        if (this.state.destFull) {
            destBadges = <div>
                <span className="badge" style={destBadgesStyle}>Type : {this.state.destFull.type}</span>

                {this.state.destFull.children && this.state.destFull.children.length && <span className="badge" style={destBadgesStyle}>Contains files :
                    <i className="fa fa-check-circle"></i>
                </span> || ""}
            </div>
        }

        let addButton = null;
        // source is a file and destination is a bucket
        if (this.state.destFull && this.state.destFull.children && this.props.state.sourceElement.length) {
            addButton = <button className="btn" style={{
                display: "block",
                margin: "auto",
                backgroundColor: "#4CAF50"
            }} onClick={this.addTransfer}>
                <i className="fa fa-plus"></i>
                Add</button>;

        }

        let sourcesList;
        if (this.props.state.sourceElement.length) {
            // Map over the transfers and get an element for each of them
            sourcesList = <ul className="list-group">{this.props.state.sourceElement.map(theSource => this.getSourceRow(theSource))}</ul>;
        } else {
            sourcesList = <h4>
                <i className="fa fa-arrow-circle-up" style={{
                    color: "#FF9900"
                }}></i>
                &nbsp;Source : No source selected
                <br/>
                <span style={infosStyle}>Sources can only be files</span>

            </h4>
        }

        return (
            <div className="panel panel-default col-md-12 " style={{
                boxShadow: "none"
            }}>
                <div className="panel panel-body">

                    <div className="row">
                        <div className="col-md-5">
                            {sourcesList}
                        </div>
                        <div className="col-md-2">
                            <i className="fa fa-long-arrow-right" style={arrowStyle}></i>
                            {addButton}
                        </div>
                        <div className="col-md-5">
                            <h4>
                                <i className="fa fa-arrow-circle-down" style={{
                                    color: "#0088CC"
                                }}></i>
                              &nbsp;Destination : {!this.state.destFull && noDestMessage}
                                {this.state.destFull && this.state.destFull.children && <span>{this.props.state.destinationElement} {destBadges}</span>}
                                {this.state.destFull && !this.state.destFull.children && <span>
                                    <i className="fa fa-times"></i>
                                    Please select a bucket</span>}

                            </h4>

                        </div>

                    </div>

                    <hr/>
                    <div className="row">
                        <TransfersViewerComponent transfers={this.props.state.transfers} startFunc={this.props.startFunc} stopFunc={this.props.stopFunc} clearFunc={this.props.clearFunc}/>
                    </div>
                </div>
            </div>
        );
    }

}

StateViewerComponent.propTypes = {
    state: React.PropTypes.object.isRequired,
    addTransferFunc: React.PropTypes.func.isRequired,
    startFunc: React.PropTypes.func.isRequired,
    stopFunc: React.PropTypes.func.isRequired,
    clearFunc: React.PropTypes.func.isRequired,
};
