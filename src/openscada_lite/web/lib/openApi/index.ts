/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/** AckAlarmMsg */
export interface AckAlarmMsg {
  /** Alarm Occurrence Id */
  alarm_occurrence_id: string;
  /**
   * Timestamp
   * @format date-time
   */
  timestamp?: string;
  /** Track Id */
  track_id?: string;
}

/** AnimationUpdateRequestMsg */
export interface AnimationUpdateRequestMsg {
  /** Datapoint Identifier */
  datapoint_identifier: string;
  /** Quality */
  quality: string;
  /**
   * Value
   * @default 0.09
   */
  value?: number;
  /** Alarm Status */
  alarm_status?: string | null;
  /** Track Id */
  track_id?: string;
}

/** ClientAlertFeedbackMsg */
export interface ClientAlertFeedbackMsg {
  /** Feedback */
  feedback: string;
  /** Track Id */
  track_id?: string;
}

/** DriverConnectCommand */
export interface DriverConnectCommand {
  /** Driver Name */
  driver_name: string;
  /** Status */
  status: string;
  /** Track Id */
  track_id?: string;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/** RawTagUpdateMsg */
export interface RawTagUpdateMsg {
  /** Datapoint Identifier */
  datapoint_identifier: string;
  /** Value */
  value: any;
  /**
   * Quality
   * @default "good"
   */
  quality?: string;
  /** Timestamp */
  timestamp?: string | null;
  /** Track Id */
  track_id?: string;
}

/** SendCommandMsg */
export interface SendCommandMsg {
  /** Command Id */
  command_id: string;
  /** Datapoint Identifier */
  datapoint_identifier: string;
  /** Value */
  value: any;
  /** Track Id */
  track_id?: string;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
}

export type QueryParamsType = Record<string | number, any>;
export type ResponseFormat = keyof Omit<Body, "body" | "bodyUsed">;

export interface FullRequestParams extends Omit<RequestInit, "body"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseFormat;
  /** request body */
  body?: unknown;
  /** base url */
  baseUrl?: string;
  /** request cancellation token */
  cancelToken?: CancelToken;
}

export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;

export interface ApiConfig<SecurityDataType = unknown> {
  baseUrl?: string;
  baseApiParams?: Omit<RequestParams, "baseUrl" | "cancelToken" | "signal">;
  securityWorker?: (
    securityData: SecurityDataType | null,
  ) => Promise<RequestParams | void> | RequestParams | void;
  customFetch?: typeof fetch;
}

export interface HttpResponse<D extends unknown, E extends unknown = unknown>
  extends Response {
  data: D;
  error: E;
}

type CancelToken = Symbol | string | number;

export enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}

export class HttpClient<SecurityDataType = unknown> {
  public baseUrl: string = "";
  private securityData: SecurityDataType | null = null;
  private securityWorker?: ApiConfig<SecurityDataType>["securityWorker"];
  private abortControllers = new Map<CancelToken, AbortController>();
  private customFetch = (...fetchParams: Parameters<typeof fetch>) =>
    fetch(...fetchParams);

  private baseApiParams: RequestParams = {
    credentials: "same-origin",
    headers: {},
    redirect: "follow",
    referrerPolicy: "no-referrer",
  };

  constructor(apiConfig: ApiConfig<SecurityDataType> = {}) {
    Object.assign(this, apiConfig);
  }

  public setSecurityData = (data: SecurityDataType | null) => {
    this.securityData = data;
  };

  protected encodeQueryParam(key: string, value: any) {
    const encodedKey = encodeURIComponent(key);
    return `${encodedKey}=${encodeURIComponent(typeof value === "number" ? value : `${value}`)}`;
  }

  protected addQueryParam(query: QueryParamsType, key: string) {
    return this.encodeQueryParam(key, query[key]);
  }

  protected addArrayQueryParam(query: QueryParamsType, key: string) {
    const value = query[key];
    return value.map((v: any) => this.encodeQueryParam(key, v)).join("&");
  }

  protected toQueryString(rawQuery?: QueryParamsType): string {
    const query = rawQuery || {};
    const keys = Object.keys(query).filter(
      (key) => "undefined" !== typeof query[key],
    );
    return keys
      .map((key) =>
        Array.isArray(query[key])
          ? this.addArrayQueryParam(query, key)
          : this.addQueryParam(query, key),
      )
      .join("&");
  }

  protected addQueryParams(rawQuery?: QueryParamsType): string {
    const queryString = this.toQueryString(rawQuery);
    return queryString ? `?${queryString}` : "";
  }

  private contentFormatters: Record<ContentType, (input: any) => any> = {
    [ContentType.Json]: (input: any) =>
      input !== null && (typeof input === "object" || typeof input === "string")
        ? JSON.stringify(input)
        : input,
    [ContentType.JsonApi]: (input: any) =>
      input !== null && (typeof input === "object" || typeof input === "string")
        ? JSON.stringify(input)
        : input,
    [ContentType.Text]: (input: any) =>
      input !== null && typeof input !== "string"
        ? JSON.stringify(input)
        : input,
    [ContentType.FormData]: (input: any) => {
      if (input instanceof FormData) {
        return input;
      }

      return Object.keys(input || {}).reduce((formData, key) => {
        const property = input[key];
        formData.append(
          key,
          property instanceof Blob
            ? property
            : typeof property === "object" && property !== null
              ? JSON.stringify(property)
              : `${property}`,
        );
        return formData;
      }, new FormData());
    },
    [ContentType.UrlEncoded]: (input: any) => this.toQueryString(input),
  };

  protected mergeRequestParams(
    params1: RequestParams,
    params2?: RequestParams,
  ): RequestParams {
    return {
      ...this.baseApiParams,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...(this.baseApiParams.headers || {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }

  protected createAbortSignal = (
    cancelToken: CancelToken,
  ): AbortSignal | undefined => {
    if (this.abortControllers.has(cancelToken)) {
      const abortController = this.abortControllers.get(cancelToken);
      if (abortController) {
        return abortController.signal;
      }
      return void 0;
    }

    const abortController = new AbortController();
    this.abortControllers.set(cancelToken, abortController);
    return abortController.signal;
  };

  public abortRequest = (cancelToken: CancelToken) => {
    const abortController = this.abortControllers.get(cancelToken);

    if (abortController) {
      abortController.abort();
      this.abortControllers.delete(cancelToken);
    }
  };

  public request = async <T = any, E = any>({
    body,
    secure,
    path,
    type,
    query,
    format,
    baseUrl,
    cancelToken,
    ...params
  }: FullRequestParams): Promise<HttpResponse<T, E>> => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.baseApiParams.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const queryString = query && this.toQueryString(query);
    const payloadFormatter = this.contentFormatters[type || ContentType.Json];
    const responseFormat = format || requestParams.format;

    return this.customFetch(
      `${baseUrl || this.baseUrl || ""}${path}${queryString ? `?${queryString}` : ""}`,
      {
        ...requestParams,
        headers: {
          ...(requestParams.headers || {}),
          ...(type && type !== ContentType.FormData
            ? { "Content-Type": type }
            : {}),
        },
        signal:
          (cancelToken
            ? this.createAbortSignal(cancelToken)
            : requestParams.signal) || null,
        body:
          typeof body === "undefined" || body === null
            ? null
            : payloadFormatter(body),
      },
    ).then(async (response) => {
      const r = response as HttpResponse<T, E>;
      r.data = null as unknown as T;
      r.error = null as unknown as E;

      const responseToParse = responseFormat ? response.clone() : response;
      const data = !responseFormat
        ? r
        : await responseToParse[responseFormat]()
            .then((data) => {
              if (r.ok) {
                r.data = data;
              } else {
                r.error = data;
              }
              return r;
            })
            .catch((e) => {
              r.error = e;
              return r;
            });

      if (cancelToken) {
        this.abortControllers.delete(cancelToken);
      }

      if (!response.ok) throw data;
      return data;
    });
  };
}

/**
 * @title OpenSCADA-Lite
 * @version 0.0.1
 */
export class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @name IndexGet
   * @summary Index
   * @request GET:/
   */
  indexGet = (params: RequestParams = {}) =>
    this.request<any, any>({
      path: `/`,
      method: "GET",
      format: "json",
      ...params,
    });

  configEditor = {
    /**
     * No description
     *
     * @tags ConfigEditor, ConfigEditor
     * @name GetConfigByName
     * @summary Get Config By Name
     * @request GET:/config-editor/api/config/{name}
     */
    getConfigByName: (name: string, params: RequestParams = {}) =>
      this.request<any, HTTPValidationError>({
        path: `/config-editor/api/config/${name}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags ConfigEditor, ConfigEditor
     * @name GetConfigs
     * @summary Get Configs
     * @request GET:/config-editor/api/configs
     */
    getConfigs: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/config-editor/api/configs`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags ConfigEditor, ConfigEditor
     * @name SaveConfig
     * @summary Save Config
     * @request POST:/config-editor/api/config
     */
    saveConfig: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/config-editor/api/config`,
        method: "POST",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags ConfigEditor, ConfigEditor
     * @name SaveConfigAs
     * @summary Save Config As
     * @request POST:/config-editor/api/saveas
     */
    saveConfigAs: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/config-editor/api/saveas`,
        method: "POST",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags ConfigEditor, ConfigEditor
     * @name Restart
     * @summary Restart App
     * @request POST:/config-editor/api/restart
     */
    restart: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/config-editor/api/restart`,
        method: "POST",
        format: "json",
        ...params,
      }),
  };
  alarm = {
    /**
     * No description
     *
     * @tags alarm
     * @name Ackalarmmsg
     * @summary Alarm/Ackalarmmsg
     * @request POST:/alarm/ackalarmmsg
     */
    ackalarmmsg: (data: AckAlarmMsg, params: RequestParams = {}) =>
      this.request<any, HTTPValidationError>({
        path: `/alarm/ackalarmmsg`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  alert = {
    /**
     * No description
     *
     * @tags alert
     * @name Clientalertfeedbackmsg
     * @summary Alert/Clientalertfeedbackmsg
     * @request POST:/alert/clientalertfeedbackmsg
     */
    clientalertfeedbackmsg: (
      data: ClientAlertFeedbackMsg,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/alert/clientalertfeedbackmsg`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  animation = {
    /**
     * No description
     *
     * @tags animation
     * @name Animationupdaterequestmsg
     * @summary Animation/Animationupdaterequestmsg
     * @request POST:/animation/animationupdaterequestmsg
     */
    animationupdaterequestmsg: (
      data: AnimationUpdateRequestMsg,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/animation/animationupdaterequestmsg`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags animation
     * @name GetSvgs
     * @summary List Svgs
     * @request GET:/animation/svgs
     */
    getSvgs: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/animation/svgs`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags animation
     * @name GetSvg
     * @summary Svg
     * @request GET:/animation/svg/{filename}
     */
    getSvg: (filename: string, params: RequestParams = {}) =>
      this.request<void, void | HTTPValidationError>({
        path: `/animation/svg/${filename}`,
        method: "GET",
        ...params,
      }),
  };
  command = {
    /**
     * No description
     *
     * @tags command
     * @name Sendcommandmsg
     * @summary Command/Sendcommandmsg
     * @request POST:/command/sendcommandmsg
     */
    sendcommandmsg: (data: SendCommandMsg, params: RequestParams = {}) =>
      this.request<any, HTTPValidationError>({
        path: `/command/sendcommandmsg`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  communication = {
    /**
     * No description
     *
     * @tags communication
     * @name Driverconnectcommand
     * @summary Communication/Driverconnectcommand
     * @request POST:/communication/driverconnectcommand
     */
    driverconnectcommand: (
      data: DriverConnectCommand,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/communication/driverconnectcommand`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  datapoint = {
    /**
     * No description
     *
     * @tags datapoint
     * @name Rawtagupdatemsg
     * @summary Datapoint/Rawtagupdatemsg
     * @request POST:/datapoint/rawtagupdatemsg
     */
    rawtagupdatemsg: (data: RawTagUpdateMsg, params: RequestParams = {}) =>
      this.request<any, HTTPValidationError>({
        path: `/datapoint/rawtagupdatemsg`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  frontend = {
    /**
     * No description
     *
     * @tags frontend
     * @name GetTabs
     * @summary Get Tabs
     * @request GET:/frontend/tabs
     */
    getTabs: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/frontend/tabs`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags frontend
     * @name Ping
     * @summary Ping
     * @request GET:/frontend/ping
     */
    ping: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/frontend/ping`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
  gis = {
    /**
     * @description Expose the GIS configuration from system_config.json.
     *
     * @tags gis
     * @name GetGisConfig
     * @summary Get Gis Config
     * @request GET:/gis/config
     */
    getGisConfig: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/gis/config`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
  streams = {
    /**
     * No description
     *
     * @tags stream
     * @name GetStreams
     * @summary List Streams
     * @request GET:/streams
     */
    getStreams: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/streams`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
  security = {
    /**
     * No description
     *
     * @tags security
     * @name GetRegisteredEndpoints
     * @summary Get Endpoints
     * @request GET:/security/endpoints
     */
    getRegisteredEndpoints: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/security/endpoints`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags security
     * @name Login
     * @summary Login
     * @request POST:/security/login
     */
    login: (
      data: Record<string, any>,
      query?: {
        /** App */
        app?: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/security/login`,
        method: "POST",
        query: query,
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags security
     * @name GetSecurityConfig
     * @summary Get Security Config
     * @request GET:/security/config
     */
    getSecurityConfig: (params: RequestParams = {}) =>
      this.request<any, any>({
        path: `/security/config`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @tags security
     * @name SaveSecurityConfig
     * @summary Save Security Config
     * @request POST:/security/config
     */
    saveSecurityConfig: (
      data: Record<string, any>,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/security/config`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
}
