class CloudMoverComponent extends React.Component {
    constructor() {
        super();

        this.state = {
            sourceElement: [],
            destinationElement: null,
            transfers: [],
            intervalId: null,
        }

        this.setSource = this.setSource.bind(this);
        this.setDestination = this.setDestination.bind(this);
        this.addTransfer = this.addTransfer.bind(this);
        this.timer = this.timer.bind(this);
        this.startTransfers = this.startTransfers.bind(this);
        this.stopTransfers = this.stopTransfers.bind(this);
        this.clearTransfers = this.clearTransfers.bind(this);
    }

    timer() {
        let toAdd = Math.floor(Math.random() * (25 - 12 + 1)) + 12;
        let transfers = this.state.transfers;

        for (var i = 0; i < transfers.length; i++) {
            if (transfers[i].progress < 100) {
                transfers[i].progress += toAdd;
                transfers[i].status = 'In progress';
                if (transfers[i].progress >= 100) {
                    transfers[i].status = 'Done';
                    transfers[i].progress = 100;
                    moveFile(transfers[i].source, transfers[i].destination);
                }
                break;
            }
        }
        this.setState(transfers : transfers);
    }

    startTransfers() {
        var intervalId = setInterval(this.timer, 1000);
        // store intervalId in the state so it can be accessed later:
        this.setState({intervalId: intervalId});
    }

    stopTransfers() {
        clearInterval(this.state.intervalId);
        this.setState({intervalId: null});
    }

    clearTransfers() {
        this.stopTransfers();
        this.setState({transfers: []});
    }

    setSource(filename) {
        var fullObject = findInMockData(filename);

        if (!fullObject.children) {
          let tmp = this.state.sourceElement;
          if (tmp.indexOf(filename) == -1)
              tmp.push(filename);
          else {
              tmp.splice(tmp.indexOf(filename), 1);
          }

          this.setState({sourceElement: tmp});
        }
    }

    setDestination(filename) {
        if (this.state.destinationElement == filename)
            this.setState({destinationElement: null});
        else
            this.setState({destinationElement: filename});
        }

    getTransferItem(source, destination) {
        const sourceFull = findInMockData(source);
        const res = {
            source: source,
            sourceProvider: "AWS",
            destination: destination,
            destinationProvider: "GCloud",
            size: sourceFull.size,
            status: 'Idle',
            progress: 0
        };
        return res;
    }

    addTransfer() {
        let transfers = this.state.transfers;
        for (var i = 0; i < this.state.sourceElement.length; i++) {
          transfers.push(this.getTransferItem(this.state.sourceElement[i], this.state.destinationElement));
        }

        this.setState({sourceElement: [], transfers: transfers});
    }

    render() {

        const awsLogoStyle = {
            margin: "0px",
            maxWidth: "200px"
        };

        const gcLogoStyle = {
            margin: "0px",
            maxWidth: "300px"
        };

        return (
            <div>
                <StateViewerComponent state={this.state} addTransferFunc={this.addTransfer} startFunc={this.startTransfers} stopFunc={this.stopTransfers} clearFunc={this.clearTransfers}/>
                <div className="panel panel-default col-md-6 ">
                    <div className="panel panel-body">
                        <div className="row" style={{
                            marginBottom: "15px"
                        }}>
                            <div className="col-lg-3 col-lg-offset-2">
                                <h4>
                                    <i className="fa fa-arrow-circle-up" style={{
                                        color: "#FF9900"
                                    }}></i>
                                    &nbsp; Select source from :
                                </h4>
                            </div>
                            <div className="col-lg-3">
                                <img src="img/s3-logo.png" style={awsLogoStyle}/>
                            </div>
                        </div>
                        <TreeViewComponent treeData={mockdata1} selectFunc={this.setSource} colorCode="#FF9900" state={this.state}/>
                    </div>
                </div>

                <div className="panel panel-default col-md-6 ">
                    <div className="panel panel-body">
                        <div className="row" style={{
                            marginBottom: "15px"
                        }}>
                            <div className="col-lg-4 col-lg-offset-1">
                                <h4>
                                    <i className="fa fa-arrow-circle-down" style={{
                                        color: "#0088CC"
                                    }}></i>
                                    &nbsp; Select destination from :
                                </h4>
                            </div>
                            <div className="col-lg-3">
                                <img src="img/google-cloud-logo-trimmed.png" style={gcLogoStyle}/>
                            </div>
                        </div>
                        <TreeViewComponent treeData={mockdata2} selectFunc={this.setDestination} state={this.state}/>
                    </div>
                </div>
            </div>
        );
    }
}
