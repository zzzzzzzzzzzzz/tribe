/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type TeamExportSkillRef = {
    name: string;
    description?: (string | null);
    managed?: boolean;
    tool_definition?: (Record<string, any> | null);
};

export type TeamExportUploadRef = {
    name: string;
    description?: (string | null);
};

export type TeamExportMember = {
    id: number;
    name: string;
    backstory?: (string | null);
    role: string;
    type: string;
    owner_of?: (number | null);
    position_x: number;
    position_y: number;
    source?: (number | null);
    provider?: string;
    model?: string;
    temperature?: number;
    interrupt?: boolean;
    base_url?: (string | null);
    skills?: Array<TeamExportSkillRef>;
    uploads?: Array<TeamExportUploadRef>;
};

export type TeamExport = {
    export_version?: number;
    id?: (number | null);
    name: string;
    description?: (string | null);
    workflow: string;
    members?: Array<TeamExportMember>;
};
