/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export const $TeamExport = {
    properties: {
        export_version: {
            type: 'number',
            default: 1,
        },
        id: {
            type: 'number',
            isNullable: true,
        },
        name: {
            type: 'string',
            isRequired: true,
        },
        description: {
            type: 'string',
            isNullable: true,
        },
        workflow: {
            type: 'string',
            isRequired: true,
        },
        members: {
            type: 'array',
            contains: {
                type: 'dictionary',
            },
        },
    },
} as const;
