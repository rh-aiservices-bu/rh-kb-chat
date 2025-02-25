export class Query {
  content: string;
  collection: string;
  collectionFullName: string;
  selectedVersion: string;
  language: string;
  type: string;

  constructor(
    content: string = '',
    collection: string = '',
    collectionFullName: string = '',
    selectedVersion: string = '',
    language: string = ''
  ) {
    this.content = content;
    this.collection = collection;
    this.collectionFullName = collectionFullName;
    this.selectedVersion = selectedVersion;
    this.language = language;
    this.type = 'Query';
  }
}

export class Answer {
  content: string[];
  type = 'Answer';

  constructor(content: string[]) {
    this.content = content;
  }
}

export class Sources {
  content: string[];
  type = 'Sources';

  constructor(content: string[]) {
    this.content = content;
  }
}

export class Message {
  content: Query | Answer | Sources;

  constructor(content: Query | Answer | Sources) {
    this.content = content;
  }
}

export class MessageHistory {
  content: Message[];

  constructor(content: Message[]) {
    this.content = content;
  }
}

export class Models {
  name: string;

  constructor(name: string) {
    this.name = name;
  }
}
