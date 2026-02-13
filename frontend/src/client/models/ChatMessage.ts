/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ChatMessageType } from './ChatMessageType';

export type ChatContentTextPart = {
    type: 'text';
    text: string;
};

export type ChatContentImagePart = {
    type: 'image_url';
    image_url: {
        url: string;
    };
};

export type ChatContentFilePart = {
    type: 'file';
    file: {
        file_id?: (string | null);
        filename?: (string | null);
        file_data?: (string | null);
    };
};

export type ChatMessage = {
    type: ChatMessageType;
    content: (string | Array<(ChatContentTextPart | ChatContentImagePart | ChatContentFilePart)>);
};
