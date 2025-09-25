import {
  Button,
  Checkbox,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useMutation, useQueryClient } from "react-query"

import {
  type ApiError,
  type UserOut,
  type UserUpdate,
  UsersService,
} from "../../client"
import useCustomToast from "../../hooks/useCustomToast"
import { emailPattern } from "../../utils"

interface EditUserProps {
  user: UserOut
  isOpen: boolean
  onClose: () => void
}

interface UserUpdateForm extends UserUpdate {
  confirm_password: string
}

const EditUser = ({ user, isOpen, onClose }: EditUserProps) => {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<UserUpdateForm>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: user,
  })

  const updateUser = async (data: UserUpdateForm) => {
    await UsersService.updateUser({ userId: user.id, requestBody: data })
  }

  const mutation = useMutation(updateUser, {
    onSuccess: () => {
      showToast("Успех!", "Пользователь успешно обновлен.", "success")
      onClose()
    },
    onError: (err: ApiError) => {
      const errDetail = err.body?.detail
      showToast("Что-то пошло не так.", `${errDetail}`, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries("users")
    },
  })

  const onSubmit: SubmitHandler<UserUpdateForm> = async (data) => {
    if (data.password === "") {
      data.password = undefined
    }
    mutation.mutate(data)
  }

  const onCancel = () => {
    reset()
    onClose()
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay />
        <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Редактировать пользователя</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isInvalid={!!errors.email}>
              <FormLabel htmlFor="email">Email</FormLabel>
              <Input
                id="email"
                {...register("email", {
                  required: "Email обязателен",
                  pattern: emailPattern,
                })}
                placeholder="Email"
                type="email"
              />
              {errors.email && (
                <FormErrorMessage>{errors.email.message}</FormErrorMessage>
              )}
            </FormControl>
            <FormControl mt={4}>
              <FormLabel htmlFor="name">Полное имя</FormLabel>
              <Input id="name" {...register("full_name")} type="text" />
            </FormControl>
            <FormControl mt={4} isInvalid={!!errors.password}>
              <FormLabel htmlFor="password">Установить пароль</FormLabel>
              <Input
                id="password"
                {...register("password", {
                  minLength: {
                    value: 8,
                    message: "Пароль должен быть не менее 8 символов",
                  },
                })}
                placeholder="Пароль"
                type="password"
              />
              {errors.password && (
                <FormErrorMessage>{errors.password.message}</FormErrorMessage>
              )}
            </FormControl>
            <FormControl mt={4} isInvalid={!!errors.confirm_password}>
              <FormLabel htmlFor="confirm_password">Подтвердите пароль</FormLabel>
              <Input
                id="confirm_password"
                {...register("confirm_password", {
                  validate: (value) =>
                    value === getValues().password ||
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
            <Flex>
              <FormControl mt={4}>
                <Checkbox {...register("is_superuser")} colorScheme="teal">
                  Суперпользователь?
                </Checkbox>
              </FormControl>
              <FormControl mt={4}>
                <Checkbox {...register("is_active")} colorScheme="teal">
                  Активный?
                </Checkbox>
              </FormControl>
            </Flex>
          </ModalBody>

          <ModalFooter gap={3}>
            <Button
              variant="primary"
              type="submit"
              isLoading={isSubmitting}
              isDisabled={!isDirty}
            >
              Сохранить
            </Button>
            <Button onClick={onCancel}>Отмена</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

export default EditUser
