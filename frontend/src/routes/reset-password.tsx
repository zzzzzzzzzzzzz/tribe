import {
  Button,
  Container,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  Text,
} from "@chakra-ui/react"
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useMutation } from "react-query"

import { type ApiError, LoginService, type NewPassword } from "../client"
import { isLoggedIn } from "../hooks/useAuth"
import useCustomToast from "../hooks/useCustomToast"

interface NewPasswordForm extends NewPassword {
  confirm_password: string
}

export const Route = createFileRoute("/reset-password")({
  component: ResetPassword,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

function ResetPassword() {
  const {
    register,
    handleSubmit,
    getValues,
    reset,
    formState: { errors },
  } = useForm<NewPasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      new_password: "",
    },
  })
  const showToast = useCustomToast()
  const navigate = useNavigate()

  const resetPassword = async (data: NewPassword) => {
    const token = new URLSearchParams(window.location.search).get("token")
    if (!token) return
    await LoginService.resetPassword({
      requestBody: { new_password: data.new_password, token: token },
    })
  }

  const mutation = useMutation(resetPassword, {
    onSuccess: () => {
      showToast("Успех!", "Пароль обновлен.", "success")
      reset()
      navigate({ to: "/login" })
    },
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Что-то пошло не так", `${errDetail}`, "error")
    },
  })

  const onSubmit: SubmitHandler<NewPasswordForm> = async (data) => {
    mutation.mutate(data)
  }

  return (
    <Container
      as="form"
      onSubmit={handleSubmit(onSubmit)}
      h="100vh"
      maxW="sm"
      alignItems="stretch"
      justifyContent="center"
      gap={4}
      centerContent
    >
      <Heading size="xl" color="ui.main" textAlign="center" mb={2}>
        Сброс пароля
      </Heading>
      <Text textAlign="center">
        Пожалуйста, введите новый пароль для вашего аккаунта.
      </Text>
      <FormControl mt={4} isInvalid={!!errors.new_password}>
        <FormLabel htmlFor="password">Set Password</FormLabel>
        <Input
          id="password"
          {...register("new_password", {
            required: "Пароль обязателен",
            minLength: {
              value: 8,
              message: "Пароль должен состоять хотя бы из 8 символов",
            },
          })}
          placeholder="Пароль"
          type="password"
        />
        {errors.new_password && (
          <FormErrorMessage>{errors.new_password.message}</FormErrorMessage>
        )}
      </FormControl>
      <FormControl mt={4} isInvalid={!!errors.confirm_password}>
        <FormLabel htmlFor="confirm_password">Подтвердить пароль</FormLabel>
        <Input
          id="confirm_password"
          {...register("confirm_password", {
            required: "Пожалуйста, подтвердите пароль",
            validate: (value) =>
              value === getValues().new_password ||
              "Пароли не совпадают",
          })}
          placeholder="Пароль"
          type="password"
        />
        {errors.confirm_password && (
          <FormErrorMessage>{errors.confirm_password.message}</FormErrorMessage>
        )}
      </FormControl>
      <Button variant="primary" type="submit">
        Сбросить пароль
      </Button>
    </Container>
  )
}

export default ResetPassword
