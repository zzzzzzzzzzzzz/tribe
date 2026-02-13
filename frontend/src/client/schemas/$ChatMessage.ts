/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ChatMessage = {
    properties: {
        type: {
            type: 'ChatMessageType',
            isRequired: true,
        },
        content: {
            anyOf: [
                {
                    type: 'string',
                },
                {
                    type: 'array',
                    contains: {
                        anyOf: [
                            {
                                properties: {
                                    type: { type: 'string', isRequired: true },
                                    text: { type: 'string', isRequired: true },
                                },
                            },
                            {
                                properties: {
                                    type: { type: 'string', isRequired: true },
                                    image_url: {
                                        properties: {
                                            url: { type: 'string', isRequired: true },
                                        },
                                        isRequired: true,
                                    },
                                },
                            },
                            {
                                properties: {
                                    type: { type: 'string', isRequired: true },
                                    file: {
                                        properties: {
                                            file_id: { type: 'string' },
                                            filename: { type: 'string' },
                                            file_data: { type: 'string' },
                                        },
                                        isRequired: true,
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
            isRequired: true,
        },
    },
} as const;
