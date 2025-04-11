import userAvatar from '@app/assets/bgimages/default-user.svg';
import orb from '@app/assets/bgimages/orb.svg';
import config from '@app/config';
import { Flex, FlexItem, FormSelect, FormSelectOption, Content } from "@patternfly/react-core";
import { t } from "i18next";
import React, { forwardRef, useImperativeHandle, Ref, useRef } from 'react';
import { Answer, MessageContent, MessageHistory, Query, Models, Source } from './classes';
import { ChatbotContent, Message, MessageBox } from '@patternfly/chatbot';


interface ChatAnswerProps {
}

export interface ChatAnswerRef {
  sendQuery: (query: Query) => void;
  resetMessageHistory: () => void;
  changeCollectionOrVersion: (selectedCollection, selectedVersion) => void;
}

const ChatAnswer = forwardRef((props: ChatAnswerProps, ref: Ref<ChatAnswerRef>) => {
  // Models
  const [llms, setLlms] = React.useState<Models[]>([]); // The list of models
  const [selectedLLM, setSelectedLlm] = React.useState<string>(''); // The selected model

  // Websocket
  const wsUrl = config.backend_api_url.replace(/http/, 'ws').replace(/\/api$/, '/ws'); // WebSocket URL
  const connection = React.useRef<WebSocket | null>(null); // WebSocket connection
  const uuid = Math.floor(Math.random() * 1000000000); // Generate a random number between 0 and 999999999

  // Chat elements
  const [answer, setAnswer] = React.useState<Answer>(new Answer([],[])); // The answer text
  const [messageHistory, setMessageHistory] = React.useState<MessageHistory>(
    new MessageHistory([
      new MessageContent(new Answer([t('chat.content.greeting')],[]))
    ])
  ); // The message history
  const chatBotAnswer = document.getElementById('chatBotAnswer'); // The chat bot answer element

  // Stopwatch and timer#
  const startTime = useRef<number | null>(null);
  const [tokens, setTokens] = React.useState<number>(0);
  const [ttft, setTtft] = React.useState<number>(0);
  const [tps, setTps] = React.useState<number>(0);

  // Open a WebSocket connection and listen for messages
  React.useEffect(() => {
    const ws = new WebSocket(wsUrl + '/query/' + uuid) || {};

    ws.onopen = () => {
      console.log('opened ws connection')
    }
    ws.onclose = (e) => {
      console.log('close ws connection: ', e.code, e.reason)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data['type'] === 'token') {
        setTokens((prevTokens) => {
          const newTokens = prevTokens + 1;
          if (newTokens === 1) {
            if (startTime.current !== null) {
              setTtft((Date.now() - startTime.current) / 1000);
            }
          }
          if (startTime.current !== null) {
            setTps(newTokens / ((Date.now() - startTime.current) / 1000));
          }
          return newTokens;
        });
        setAnswer(answer => new Answer(
          [...(answer?.content || []), data['token']],
          [...(answer?.sources || [])]
        ));
        return;
      } else if (data['type'] === 'source') {
        setAnswer(answer => {
          const existingSourceIndex = answer?.sources?.findIndex(source => source.content === data['source']);
          if (existingSourceIndex !== -1) {
            // Update the score if the new score is higher
            const updatedSources = [...answer.sources];
            updatedSources[existingSourceIndex].score = Math.max(updatedSources[existingSourceIndex].score, data['score']);
            return new Answer(
              [...(answer?.content || [])],
              updatedSources
            );
          } else {
            // Add the new source if it doesn't exist
            return new Answer(
              [...(answer?.content || [])],
              [...(answer?.sources || []), new Source(data['source'], data['score'])]
            );
          }
        });
        return;
      }
    }

    connection.current = ws;

    // Clean up function
    return () => {
      if (connection.current) {
        connection.current.close();
        console.log('WebSocket connection closed');
      }
    };
  }, []);

  React.useEffect(() => {
    console.log('Updated answer: ', answer);
  }, [answer]);


  // Load available models at startup
  React.useEffect(() => {
    const fetchLLMs = async () => {
      const response = await fetch(`${config.backend_api_url}/llms`);
      const data = await response.json();
      setLlms(data);
      setSelectedLlm(data[0].name);
    }
    fetchLLMs();
  }
    , []);

  // Scroll to the bottom of the chat window when the answer changes
  React.useEffect(() => {
    if (chatBotAnswer) {
      chatBotAnswer.scrollTop = chatBotAnswer.scrollHeight;
    }
  }, [answer, messageHistory]);  // Dependency array


  /**
   * Sends the query text to the server via WebSocket.
   * Saves the previous response, sources, query, and message history, and create a new Message History from them.
   * Clears the query text, previous response, and previous sources.
   * If the query text is empty, sets the previous response to ['Please enter a query...'].
   */
  const sendQuery = (query: Query) => {
    if (connection.current?.readyState === WebSocket.OPEN) {
      const previousAnswer = new MessageContent(new Answer(answer.content,answer.sources)); // Save the previous response, needed because states are updated asynchronously
      const previousQuery = new MessageContent(new Query(query.content)); // Save the previous query
      const previousMessageHistory = new MessageHistory(messageHistory.message); // Save the previous message history
      setMessageHistory(new MessageHistory([...previousMessageHistory.message, previousAnswer, previousQuery])); // Add the previous response to the message history
      setAnswer(new Answer([],[])); // Clear the previous response
      setTokens(0);
      setTps(0);
      setTtft(0);
      // Put the query in a JSON object so that we can add other info later
      if (query.content !== "") {
        let data = {
          model: selectedLLM,
          query: query.content,
          collection: query.collection,
          collection_full_name: query.collectionFullName,
          version: query.selectedVersion,
          language: query.language
        };
        startTime.current = Date.now();
        connection.current?.send(JSON.stringify(data)); // Send the query to the server
      } else {
        setAnswer(new Answer([t('chat.content.empty_query')],[]));
      }
    };
  }

  /**
   * Resets the message history, answer sources, and answer text.
   * If a selected collection is provided, it sets the message history with a message about the selected collection and version.
   * If no collection is selected, it sets the message history with a default greeting message.
   */
  const resetMessageHistory = () => {
    setMessageHistory(new MessageHistory([
      new MessageContent(new Answer([t('chat.content.greeting')],[]))
    ]));
    setAnswer(new Answer([''],[])); // Clear the previous response
  };

  const changeCollectionOrVersion = (selectedCollection, selectedVersion) => {
    const previousAnswer = new MessageContent( // Save the previous response, needed because states are updated asynchronously
      new Answer(answer.content,answer.sources)
    );
    const previousMessageHistory = new MessageHistory(messageHistory.message); // Save the previous message history
    if (selectedCollection.collection_full_name !== "None") {
      setMessageHistory(new MessageHistory(
        [...previousMessageHistory.message,
          previousAnswer,
        new MessageContent(new Answer(
          [t('chat.content.change_product_prompt_start') + ' **' + selectedCollection.collection_full_name + '** ' + t('chat.content.change_product_prompt_version') + ' **' + selectedVersion + '**.'],
          []
        ))
        ]
      ));
    } else {
      setMessageHistory(new MessageHistory(
        [...previousMessageHistory.message,
          previousAnswer,
        new MessageContent(new Answer(
          [t('chat.content.change_product_prompt_none')],[]
        ))
        ]
      ));
    }
    setAnswer(new Answer([],[])); // Clear the previous response
  }

  useImperativeHandle(ref, () => ({
    sendQuery(query) {
      sendQuery(query);
    },
    resetMessageHistory() {
      resetMessageHistory();
    },
    changeCollectionOrVersion(selectedCollection, selectedVersion) {
      changeCollectionOrVersion(selectedCollection, selectedVersion);
    }
  }));

  const onChangeLlm = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setSelectedLlm(value);
  }

  /**
   * Converts a cosine similarity score to a percentage.
   *
   * The function clamps the input score to the range [0, 2] and then
   * converts it to a percentage where a score of 2 corresponds to 0%
   * and a score of 0 corresponds to 100%.
   *
   * @param score - The cosine similarity score to convert.
   * @returns The corresponding percentage value.
   */
  const cosineScoreToPercentage = (score: number): number => {

    const clampedScore = Math.max(0, Math.min(2, score));
    return Math.round((1 - clampedScore / 2) * 100);
  }

  return (
    <Flex direction={{ default: 'column' }} className='chat-item'>
      <FlexItem >
        <Flex direction={{ default: 'row' }} className='chat-llm-select'>
          <Content component='h3' className='model-title'>Model:</Content>
          <FormSelect
            value={selectedLLM}
            onChange={onChangeLlm}
            aria-label="FormSelect Input"
            ouiaId="BasicFormSelectCategory"
            className='chat-llm-select'
          >
            {llms && llms.map((llm, index) => (
              <FormSelectOption key={index} value={llm.name} label={llm.name} />
            ))}
          </FormSelect>
          <Content className='chat-llm-stats'>
            {ttft !== 0 && (
              <Content component="p" className='chat-llm-stats'>{ttft.toFixed(2)}s tft,</Content>
            )}
            {tps !== 0 && (
              <Content component="p" className='chat-llm-stats'>{tps.toFixed(2)} t/s</Content>
            )}
          </Content>
        </Flex>
      </FlexItem>
      <FlexItem className='chat-bot-answer'>
        <ChatbotContent className='chat-bot-answer-content'>
        <MessageBox id='chatBotAnswer'>
          {/* Message History rendering */}
          {messageHistory.message.map((message: MessageContent, index) => {
            const renderMessage = () => {
              if (message.messageContent.content.length != 0) {
                if (message.messageContent.type === "Query" && message.messageContent.content != "") { // If the message is a query
                  return (
                  <Message
                    name="User"
                    role="user"
                    content={Array.isArray(message.messageContent.content) ? message.messageContent.content.join(' ') : message.messageContent.content}
                    timestamp="1 hour ago"
                    avatar={userAvatar}
                    />
                    );
                } else if (message.messageContent.type === "Answer" && (message.messageContent.content as string[]).join("") != "") { // If the message is a response
                    return(
                    <Message
                    name="Bot"
                    role="bot"
                    content={(message.messageContent.content as string[]).join("")}
                    timestamp="1 hour ago"
                    avatar={orb}
                    {...(message.messageContent.type === "Answer" && 'sources' in message.messageContent && message.messageContent.sources?.length > 0 && {
                      sources: {
                      sources: message.messageContent.sources.map((source) => ({
                        title: `${source.content.substring(source.content.lastIndexOf('/') + 1)} (${cosineScoreToPercentage(source.score)}%)`,
                        link: source.content,
                        })),
                      },
                    })}
                    />
                    );
                } else {
                  {/* If the message is of an unknown type */ }
                  return;
                }
              } else {
                {/* If the message is empty */ }
                return;
              }
            }
            return (
              <React.Fragment key={index}>
                {renderMessage()}
              </React.Fragment>
            );
          })}

          {/* New Answer rendering */}
          {answer.content.join("") !== "" && (
            <Message
            name="Bot"
            role="bot"
            content={(answer.content as string[]).join("")}
            timestamp="1 hour ago"
            avatar={orb}
            {...(answer.sources?.length > 0 && {
              sources: {
              sources: answer.sources.map((source) => ({
                title: `${source.content.substring(source.content.lastIndexOf('/') + 1)} (${cosineScoreToPercentage(source.score)}%)`,
                link: source.content,
                })),
              },
            })}
            />
          )}
        </MessageBox>
        </ChatbotContent>
      </FlexItem>
    </Flex>
  );
})

export default ChatAnswer;