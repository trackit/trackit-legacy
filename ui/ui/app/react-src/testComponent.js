class HelloComponent extends React.Component {
  constructor() {
    super();
    this.state = {text: 'aaaaaaaa'};
  }

  render() {
    return (
      <span>Hello world this is {this.state.text} </span>
    );
  }
}
