import {
  Box,
  Button,
  Container,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  useColorModeValue,
} from "@chakra-ui/react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useMutation } from "react-query"

import { type ApiError, type UpdatePassword, UsersService } from "../../client"
import useCustomToast from "../../hooks/useCustomToast"

interface UpdatePasswordForm extends UpdatePassword {
  confirm_password: string
}

const ChangePassword = () => {
  const color = useColorModeValue("inherit", "ui.white")
  const showToast = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<UpdatePasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
  })

  const UpdatePassword = async (data: UpdatePassword) => {
    await UsersService.updatePasswordMe({ requestBody: data })
  }

  const mutation = useMutation(UpdatePassword, {
    onSuccess: () => {
      showToast("Успех!", "Пароль успешно обновлен.", "success")
      reset()
    },
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Что-то пошло не так.", `${errDetail}`, "error")
    },
  })

  const onSubmit: SubmitHandler<UpdatePasswordForm> = async (data) => {
    mutation.mutate(data)
  }

  return (
    <>
      <Container maxW="full" as="form" onSubmit={handleSubmit(onSubmit)}>
        <Heading size="sm" py={4}>
          Изменить пароль
        </Heading>
        <Box w={{ sm: "full", md: "50%" }}>
          <FormControl isRequired isInvalid={!!errors.current_password}>
                        <FormLabel color={color} htmlFor="current_password">
              Текущий пароль
            </FormLabel>
            <Input
              id="current_password"
              {...register("current_password", {
                required: "Текущий пароль обязателен",
                minLength: 8,
              })}
              type="password"
            />
            {errors.current_password && (
              <FormErrorMessage>
                {errors.current_password.message}
              </FormErrorMessage>
            )}
          </FormControl>
          <FormControl isInvalid={!!errors.new_password} mt={4}>
            <FormLabel color={color} htmlFor="new_password">
              Новый пароль
            </FormLabel>
            <Input
              id="new_password"
              {...register("new_password", {
                required: "Пароль обязателен",
                minLength: {
                  value: 8,
                  message: "Пароль должен быть не менее 8 символов",
                },
              })}
              placeholder="Пароль"
              type="password"
            />
            {errors.new_password && (
              <FormErrorMessage>{errors.new_password.message}</FormErrorMessage>
            )}
          </FormControl>
          <FormControl mt={4} isRequired isInvalid={!!errors.confirm_password}>
            <FormLabel htmlFor="confirm_password">Подтвердите пароль</FormLabel>
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
              <FormErrorMessage>
                {errors.confirm_password.message}
              </FormErrorMessage>
            )}
          </FormControl>
          <Button
            variant="primary"
            mt={4}
            type="submit"
            isLoading={isSubmitting}
          >
            Сохранить
          </Button>
        </Box>
      </Container>
    </>
  )
}
export default ChangePassword
