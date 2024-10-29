import React from 'react'


class GPTChat extends React.Component {

  state = {
    input: '',
    conversation: null,
  }

  websocket = null;

  handleInputChange = (event) => {
    this.setState({input: event.target.value});
  };

  handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault(); // Prevent the default action to avoid adding a newline
      this.handleSendMessage(event);
    }
  };

  handleSendMessage = (event) => {
    event.preventDefault();
    const message = this.state.input;

    this.props.addChatMessage(this.props.chatIdentifier, "user", message)

    // Send message to server
    if (!this.websocket) {

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const chatArgs = new URLSearchParams({
        'objType': this.props.obj ? this.props.obj.type : '',
        'objPk': this.props.obj ? this.props.obj.pk : '',
        'phrasePk': this.props.phraseObj.pk,
      }).toString();
      const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.props.articlePk}?${chatArgs}`;
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onmessage = (event) => {
        const response = JSON.parse(event.data);
        this.props.addChatMessage(this.props.chatIdentifier, "assistant", response.message)
      };

      this.websocket.onopen = () => {
        // Send the entire history to server (if any), since it only has context for the active websocket connection
        this.websocket.send(JSON.stringify({resetConversation: this.props.conversation}));
      };

    } else {
      this.websocket.send(JSON.stringify({message: message}));
    }

    // Clear the input field
    this.setState(prevState => ({
      input: ''
    }));

  };

  componentWillUnmount() {
    if (this.websocket !== null) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  render() {

    return (
      <div>

        <h2 className="font-bold text-lg text-zinc-400 mt-3 hidden md:block">Ask GPT</h2>
        <div className="">
          {
            this.props.conversation.map((msg, index) => (

              <div key={index}
                   className={`mt-2 mb-2 ${msg.sender === 'user' ? 'ml-8 bg-blue-50 text-blue-900' : 'mr-8 bg-zinc-100'} p-3 rounded-md`}>
                  <span className="text-sm">
                    {msg.message.split('\n').map((part, index) => (
                      <React.Fragment key={index}>
                        {part}
                        {index !== msg.message.split('\n').length - 1 && <br/>}
                      </React.Fragment>
                    ))}
                  </span>
              </div>

            ))
          }
        </div>


        <form className="md:mt-1 md:mb-4" onSubmit={this.handleSendMessage}>
        <textarea
          className={[
            "w-full rounded-md !outline-none focus:outline-none focus:ring-offset-0 focus:ring-0",
            // 16px is the minimum that iOS doesn't auto-zoom when you focus the input field
            this.props.isMobile ? "h-16 text-[16px] border-zinc-200 focus:border-zinc-300" :
              "h-24 text-sm border-zinc-400 focus:border-zinc-800",
          ].join(' ')}
          enterKeyHint="send"
          value={this.state.input}
          onChange={this.handleInputChange}
          onKeyDown={this.handleKeyDown}
          placeholder={this.props.obj ? "Ask anything about this word or sentence" : "Ask anything about this sentence"}></textarea>
          {
            <div className="text-right">
              <button type="submit" className="rounded-md px-3 py-2 font-semibold text-zinc-500 bg-zinc-100 shadow-sm hover:bg-zinc-200">
                Send
              </button>
            </div>
          }
        </form>

      </div>

    )
  }
}

export default GPTChat

