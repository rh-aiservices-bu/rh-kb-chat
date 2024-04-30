import userAvatar from '@app/assets/bgimages/avatar-user.svg';
import orb from '@app/assets/bgimages/orb.svg';
import config from '@app/config';
import { faCommentDots, faPaperPlane } from '@fortawesome/free-regular-svg-icons';
import { faPlusCircle } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { Button, Card, CardBody, CardHeader, Flex, FlexItem, FormSelect, FormSelectOption, Grid, GridItem, Page, PageSection, Panel, PanelMain, PanelMainBody, Stack, StackItem, Text, TextArea, TextContent, TextVariants, Tooltip } from '@patternfly/react-core';
import * as React from 'react';
import Markdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';


/**
 * Represents the Chat component.
 *
 * @component
 * @param {Object} props - The component props.
 * @param {string} props.claimSummary - The claim summary.
 * @returns {JSX.Element} The rendered Chat component.
 */
const Chat: React.FunctionComponent<{ claimSummary: string }> = ({ claimSummary }) => {

  class Query {
    content: string;

    constructor(content: string) {
      this.content = content;
    }
  }

  class Answer {
    content: string[];

    constructor(content: string[]) {
      this.content = content;
    }
  }

  class Sources {
    content: string[];

    constructor(content: string[]) {
      this.content = content;
    }
  }

  class Message {
    content: Query | Answer | Sources;

    constructor(content: Query | Answer | Sources) {
      this.content = content;
    }
  }

  class MessageHistory {
    content: Message[];

    constructor(content: Message[]) {
      this.content = content;
    }
  }

  type Collection = {
    product: string;
    product_full_name: string;
    version: string[];
    language: string;
  };

  type MarkdownRendererProps = {
    children: string;
  };

  // Websocket
  const wsUrl = config.backend_api_url.replace(/http/, 'ws').replace(/\/api$/, '/ws'); // WebSocket URL
  const connection = React.useRef<WebSocket | null>(null); // WebSocket connection

  // Collection elements
  const [collections, setCollections] = React.useState<Collection[]>([]); // The collections
  const [product, setProduct] = React.useState<string>('None'); // The selected product
  const [versions, setVersions] = React.useState<string[]>([]); // The versions for this product
  const [selectedVersion, setSelectedVersion] = React.useState<string>(''); // The selected version
  const [language, setLanguage] = React.useState<string>(''); // The selected language
  const [selectedCollection, setSelectedCollection] = React.useState<string>('none'); // Default collection name

  // Chat elements
  const [queryText, setQueryText] = React.useState<Query>(new Query('')); // The query text
  const [answerText, setAnswerText] = React.useState<Answer>(new Answer([''])); // The answer text
  const [answerSources, setAnswerSources] = React.useState<Sources>(new Sources([])); // Array of sources for the answer
  const [messageHistory, setMessageHistory] = React.useState<MessageHistory>(
    new MessageHistory([
      new Message(new Answer(['Hi! I am your documentation Assistant. How can I help you today?']))
    ])
  ); // The message history
  const chatBotAnswer = document.getElementById('chatBotAnswer'); // The chat bot answer element

  // Loads the collections from the backend on startup
  React.useEffect(() => {
    const fetchCollections = async () => {
      const response = await fetch(`${config.backend_api_url}/collections`);
      const data = await response.json();
      setCollections(data);
    }
    fetchCollections();
  }, []);

  // Open a WebSocket connection and listen for messages
  React.useEffect(() => {
    const ws = new WebSocket(wsUrl + '/query') || {};

    ws.onopen = () => {
      console.log('opened ws connection')
    }
    ws.onclose = (e) => {
      console.log('close ws connection: ', e.code, e.reason)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data['type'] === 'token') {
        setAnswerText(answerText => new Answer([...answerText.content, data['token']]));
        return;
      } else if (data['type'] === 'source') {
        setAnswerSources(answerSources => new Sources([...answerSources.content, data['source']]));
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
  }, [])

  // Scroll to the bottom of the chat window when the answer changes
  React.useEffect(() => {
    if (chatBotAnswer) {
      chatBotAnswer.scrollTop = chatBotAnswer.scrollHeight;
    }
  }, [answerText, answerSources]);  // Dependency array


  /**
   * Sends the query text to the server via WebSocket.
   * Saves the previous response, sources, query, and message history, and create a new Message History from them.
   * Clears the query text, previous response, and previous sources.
   * If the query text is empty, sets the previous response to ['Please enter a query...'].
   */
  const sendQueryText = () => {
    if (connection.current?.readyState === WebSocket.OPEN) {
      const previousAnswer = new Message(new Answer(answerText.content)); // Save the previous response, needed because states are updated asynchronously
      const previousSources = new Message(new Sources(answerSources.content)); // Save the previous sources
      const previousQuery = new Message(new Query(queryText.content)); // Save the previous query
      const previousMessageHistory = new MessageHistory(messageHistory.content); // Save the previous message history
      setMessageHistory(new MessageHistory([...previousMessageHistory.content, previousAnswer, previousSources, previousQuery])); // Add the previous response to the message history
      setQueryText(new Query('')); // Clear the query text
      setAnswerText(new Answer([])); // Clear the previous response
      setAnswerSources(new Sources([])); // Clear the previous sources
      // Put the query in a JSON object so that we can add other info later
      if (queryText.content !== "") {
        var product_full_name = "";
        if (selectedCollection !== 'none') {
          product_full_name = collections.find(collection => collection.product === product)?.product_full_name ?? "";
        }
        let data = {
          query: queryText.content,
          collection: selectedCollection,
          product_full_name: product_full_name,
          version: selectedVersion,
        };
        connection.current?.send(JSON.stringify(data)); // Send the query to the server
      } else {
        setAnswerText(new Answer(['Please enter a query...']));
      }
    };
  }

  /**
   * Resets the message history, answer sources, and answer text.
   * If a selected collection is provided, it sets the message history with a message about the selected collection and version.
   * If no collection is selected, it sets the message history with a default greeting message.
   */
  const resetMessageHistory = () => {
    setMessageHistory(new MessageHistory([]));
    setAnswerSources(new Sources([]));
    setAnswerText(new Answer(['']));
    const collection = collections.find(collection => collection.product === product);
    if (collection?.product_full_name !== "None") {
      setMessageHistory(new MessageHistory([
        new Message(
          new Answer(
            ['We are talking about **' + collection?.product_full_name + '** version **' + collection?.version + '**. Ask me any question!']
          )
        )
      ]));
    } else {
      setMessageHistory(new MessageHistory([
        new Message(
          new Answer(['We are not talking about any specific product. Please choose one or tell me how can I help you!'])
        )
      ])
      );
    }
  };

  /**
   * Updates the collection based on the selected collection and version.
   * @param selectedCollection - The selected collection.
   * @param selectedVersion - The selected version.
   */
  const updateCollection = (selectedCollection: Collection, selectedVersion: string) => {
    setVersions(selectedCollection.version);
    setSelectedVersion(selectedVersion);
    setLanguage(selectedCollection.language);
    let collection_name = selectedCollection.product + '_' + selectedCollection.language + '_' + selectedVersion;
    setSelectedCollection(collection_name.replace(/[.-]/g, '_'));
    const previousAnswer = new Message( // Save the previous response, needed because states are updated asynchronously
      new Answer(answerText.content)
    );
    const previousSources = new Message( // Save the previous sources
      new Sources(answerSources.content)
    );
    const previousMessageHistory = new MessageHistory(messageHistory.content); // Save the previous message history
    if (selectedCollection.product_full_name !== "None") {
      setMessageHistory(new MessageHistory(
        [...previousMessageHistory.content,
          previousAnswer,
          previousSources,
        new Message(new Answer(
          ['Ok, we are now talking about **' + selectedCollection.product_full_name + '** version **' + selectedVersion + '**.']
        ))
        ]
      ));
    } else {
      setMessageHistory(new MessageHistory(
        [...previousMessageHistory.content,
          previousAnswer,
          previousSources,
        new Message(new Answer(
          ['Ok, we are not talking about any specific product.']
        ))
        ]
      ));
    }

    setAnswerText(new Answer([])); // Clear the previous response
    setAnswerSources(new Sources([])); // Clear the previous sources
  }

  /**
   * Handles the change event of the product select element.
   * @param _event - The form event object.
   * @param value - The selected value from the product select element.
   */
  const onChangeProduct = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setProduct(value);
    const collection = collections.find(collection => collection.product === value);
    if (collection) {
      const version = collection.version[0];
      updateCollection(collection, version);
    }
  }

  /**
   * Handles the change event of the version select element.
   * 
   * @param _event - The form event object.
   * @param value - The selected value from the version select element.
   */
  const onChangeVersion = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setSelectedVersion(value);
    const collection = collections.find(collection => collection.product === product);
    if (collection) {
      const version = value;
      updateCollection(collection, version);
    }
  }

  /**
   * Handles the change event of the language select element.
   * @param event - The change event.
   * @param value - The selected value.
   */
  const onChangeLanguage = (event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setLanguage(value);
    let collection_name = product + '_' + language + '_' + selectedVersion;
    setSelectedCollection(collection_name.replace(/[.-]/g, '_'));
  }

  /**
   * Renders markdown content with syntax highlighting for code blocks.
   * 
   * @param markdown - The markdown content to render.
   * @returns The rendered markdown content.
   */
  const MarkdownRenderer = ({ children: markdown }: MarkdownRendererProps) => {
    return (
      <Markdown className='chat-question-text'
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');

            return !inline && match ? (
              <SyntaxHighlighter style={dracula} PreTag="div" language={match[1]} {...props}>
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className='chat-question-text' {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {markdown}
      </Markdown>
    );
  }


  return (
    <Page>
      <PageSection>
        <Flex direction={{ default: 'column' }}>

          {/* Product, version and language selectors */}
          <FlexItem>
            <Flex>
              <FlexItem>
                <Flex direction={{ default: 'column' }}>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h3} >Product</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <FormSelect
                      value={product}
                      onChange={onChangeProduct}
                      aria-label="FormSelect Input"
                      ouiaId="BasicFormSelectCategory"
                      className="collection-select"
                    >
                      {collections && collections.map((collection, index) => (
                        <FormSelectOption key={index} value={collection.product} label={collection.product_full_name} />
                      ))}
                    </FormSelect>
                  </FlexItem>
                </Flex>
              </FlexItem>
              <FlexItem>
                <Flex direction={{ default: 'column' }}>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h3} >Version</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <FormSelect
                      value={selectedVersion}
                      onChange={onChangeVersion}
                      aria-label="FormSelect Input"
                      ouiaId="BasicFormSelectCategory"
                      className='version-language-select'
                    >
                      {versions && versions.map((version, index) => (
                        <FormSelectOption key={index} value={version} label={version} />
                      ))}
                    </FormSelect>
                  </FlexItem>
                </Flex>
              </FlexItem>
              <FlexItem>
                <Flex direction={{ default: 'column' }}>
                  <FlexItem>
                    <TextContent>
                      <Text component={TextVariants.h3} >Language</Text>
                    </TextContent>
                  </FlexItem>
                  <FlexItem>
                    <FormSelect
                      value={language}
                      onChange={onChangeLanguage}
                      aria-label="FormSelect Input"
                      ouiaId="BasicFormSelectCategory"
                      className='version-language-select'
                    >
                      <FormSelectOption key={0} value={language} label={language} />
                    </FormSelect>
                  </FlexItem>
                </Flex>
              </FlexItem>
              {/* Uncomment the following code to display the collection name */}
              {/*                     <FlexItem>
                                <TextContent>
                                    <Text component={TextVariants.p} className=''>
                                        {collection}
                                    </Text>
                                </TextContent>
                            </FlexItem> */}
            </Flex>
          </FlexItem>

          {/* Chat Window */}
          <FlexItem className='flex-chat'>
            <Card isRounded className='chat-card'>
              <CardHeader className='chat-card-header'>
                <TextContent>
                  <Text component={TextVariants.h3} className='chat-card-header-title'><FontAwesomeIcon icon={faCommentDots} />&nbsp;Documentation Assistant</Text>
                </TextContent>
              </CardHeader>
              <CardBody className='chat-card-body'>
                <Stack>
                  <StackItem isFilled className='chat-bot-answer' id='chatBotAnswer'>
                    <TextContent>

                      {/* Message History rendering */}
                      {messageHistory.content.map((message: Message, index) => {
                        const renderMessage = () => {
                          if (message.content.content.length != 0) {
                            if (message.content.constructor.name === "Query" && message.content.content != "") { // If the message is a query
                              return <Grid className='chat-item'>
                                <GridItem span={1} className='grid-item-orb'>
                                  <img src={userAvatar} className='user-avatar' />
                                </GridItem>
                                <GridItem span={11}>
                                  <Text component={TextVariants.p} className='chat-question-text'>{message.content.content}</Text>
                                </GridItem>
                              </Grid>
                            } else if (message.content.constructor.name === "Answer" && (message.content.content as string[]).join("") != "") { // If the message is a response
                              return <Grid className='chat-item'>
                                <GridItem span={1} className='grid-item-orb'>
                                  <img src={orb} className='orb' />
                                </GridItem>
                                <GridItem span={11}>
                                  <MarkdownRenderer>{(message.content.content as string[]).join("")}</MarkdownRenderer>
                                </GridItem>
                              </Grid>
                            } else if (message.content.constructor.name === "Sources") { // If the message is a source
                              return <Grid className='chat-item'>
                                <GridItem span={1} className='grid-item-orb'>&nbsp;</GridItem>
                                <GridItem span={11}>
                                  <Text component={TextVariants.p} className='chat-source-text'>{"References: "}</Text>
                                  {message.content && (message.content.content as string[]).map((source, index) => {
                                    const renderSource = () => {
                                      if (source.startsWith('http')) {
                                        return <Text component={TextVariants.p} className='chat-source-text'>
                                          <a href={source} target="_blank" className='chat-source-link'>{source}</a>
                                        </Text>
                                      } else {
                                        return <Text component={TextVariants.p} className='chat-source-text'>{source}</Text>
                                      }
                                    };
                                    return (
                                      <React.Fragment key={index}>
                                        {renderSource()}
                                      </React.Fragment>
                                    );
                                  })}
                                </GridItem>
                              </Grid>
                            } else {
                              console.log('Unknown message type: ' + message.content.constructor.name);
                              return;
                            }
                          } else {
                            console.log('Empty message');
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
                      {answerText.content.join("") !== "" && (
                        <Grid className='chat-item'>
                          <GridItem span={1} className='grid-item-orb'>
                            <img src={orb} className='orb' />
                          </GridItem>
                          <GridItem span={11}>
                            <MarkdownRenderer>{answerText.content.join("")}</MarkdownRenderer>
                            <Text component={TextVariants.p} className='chat-source-text'>{answerSources.content.length != 0 && "References: "}</Text>
                            {answerSources && answerSources.content.map((source, index) => {
                              const renderSource = () => {
                                if (source.startsWith('http')) {
                                  return <Text component={TextVariants.p} className='chat-source-text'>
                                    <a href={source} target="_blank" className='chat-source-link'>{source}</a>
                                  </Text>
                                } else {
                                  return <Text component={TextVariants.p} className='chat-source-text'>{source}</Text>
                                }
                              };
                              return (
                                <React.Fragment key={index}>
                                  {renderSource()}
                                </React.Fragment>
                              );
                            })}

                          </GridItem>
                        </Grid>
                      )}
                    </TextContent>
                  </StackItem>

                  {/* Input section */}
                  <StackItem className='chat-input-panel'>
                    <Panel variant="raised">
                      <PanelMain>
                        <PanelMainBody className='chat-input-panel-body'>
                          <TextArea
                            value={queryText.content}
                            type="text"
                            onChange={event => {
                              setQueryText({ ...queryText, content: event.target.value });
                            }}
                            aria-label="query text input"
                            placeholder='Ask me anything...'
                            onKeyDown={event => {
                              if (event.key === 'Enter') {
                                event.preventDefault();
                                sendQueryText();
                              }
                            }}
                          />
                          <Flex>
                            <FlexItem>
                              <Tooltip
                                content={<div>Start a new chat</div>}
                              >
                                <Button variant="link" onClick={resetMessageHistory} aria-label='StartNewChat'><FontAwesomeIcon icon={faPlusCircle} /></Button>
                              </Tooltip>
                            </FlexItem>
                            <FlexItem align={{ default: 'alignRight' }}>
                              <Tooltip
                                content={<div>Send your query</div>}
                              >
                                <Button variant="link" onClick={sendQueryText} aria-label='SendQuery'><FontAwesomeIcon icon={faPaperPlane} /></Button>
                              </Tooltip>
                            </FlexItem>

                          </Flex>
                        </PanelMainBody>
                      </PanelMain>
                    </Panel>
                  </StackItem>
                  <StackItem>
                    <TextContent>
                      <Text className='chat-disclaimer'>This assistant is powered by an AI. It may display inaccurate info, so please double-check the responses.</Text>
                    </TextContent>
                  </StackItem>
                </Stack>
              </CardBody>
            </Card >
          </FlexItem>
        </Flex>
      </PageSection>
    </Page>
  );
}

export { Chat };
