class TransfersViewerComponent extends React.Component {

    getTransferRow(transfer) {

        /*const actGroup =
      <div className="btn-group btn-group-xs user-actions">
        <ListKeysButton username={user.UserName}/>
        <DeleteUserButton
          username={user.UserName}
          callback={this.refresh}/>
      </div>;*/

        return (
            <tr key={transfer.source}>
                <td style={{
                    fontWeight: 'bold',
                    paddingLeft: '25px'
                }}>
                    <span style={{
                        color: "#FF9900"
                    }}>{transfer.sourceProvider}</span>
                    &nbsp; {transfer.source}
                </td>
                <td style={{
                    fontWeight: 'bold'
                }}>
                    <span style={{
                        color: "#0088CC"
                    }}>{transfer.destinationProvider}</span>
                    &nbsp; {transfer.destination}
                </td>
                <td >
                    {bytesToSize(transfer.size)}
                </td>
                <td>
                    <div className="progress" style={{
                        minWidth: "400px"
                    }}>
                        <div className="progress-bar progress-bar-success progress-bar-striped active" role="progressbar" aria-valuenow={transfer.progress} aria-valuemin="0" aria-valuemax="100" style={{
                            width: transfer.progress + "%"
                        }}>
                            <span >{transfer.progress}% Complete</span>
                        </div>
                    </div>
                </td>
                <td>
                    {transfer.status}
                </td>
            </tr>
        );
    }

    startTransfers() {}

    render() {
        let transfersList;
        if (this.props.transfers.length) {
            // Map over the transfers and get an element for each of them
            transfersList = this.props.transfers.map(transfer => this.getTransferRow(transfer));
        } else {
            return (
                <h4 style={{
                    textAlign: "center"
                }}>No current transfers.</h4>
            );
        }

        return (
            <div>
                <div className="btn-group">
                    <button className="btn" onClick={this.props.startFunc} style={{
                        backgroundColor: "#4CAF50",
                        marginLeft: "15px",
                    }}>
                        <i className="fa fa-play"></i>
                        &nbsp;Start
                    </button>
                    <button className="btn" onClick={this.props.stopFunc} style={{
                        backgroundColor: "#4CAF50"
                    }}>
                        <i className="fa fa-stop"></i>
                        &nbsp;Stop
                    </button>
                </div>
                <button className="btn" onClick={this.props.clearFunc} style={{
                    backgroundColor: "#4CAF50",
                    marginLeft: "15px",
                }}>
                    <i className="fa fa-times"></i>
                    &nbsp;Clear
                </button>

                <table className="table table-striped">
                    <thead>
                        <tr>
                            <th>Source</th>
                            <th>Destination</th>
                            <th>Size</th>
                            <th>Progress</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transfersList}
                    </tbody>
                </table>
            </div>
        );
    }
}

TransfersViewerComponent.propTypes = {
    transfers: React.PropTypes.array.isRequired,
    startFunc: React.PropTypes.func.isRequired,
    stopFunc: React.PropTypes.func.isRequired,
    clearFunc: React.PropTypes.func.isRequired
}
